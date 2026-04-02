"""
HDLC Segmented Frame Handling.

This module provides functionality for handling segmented HDLC frames,
where large information fields are split across multiple frames.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import structlog

from dlms_cosem.hdlc import exceptions as hdlc_exceptions

LOG = structlog.get_logger()


@dataclass
class SegmentedFrameInfo:
    """
    Information about a segmented frame transmission.

    Attributes:
        source_address: Source address of the frames
        destination_address: Destination address of the frames
        total_segments: Total number of segments (if known)
        received_segments: List of received segment data
        segment_numbers: List of segment numbers received
        is_complete: Whether all segments have been received
    """
    source_address: int
    destination_address: int
    total_segments: Optional[int] = None
    received_segments: List[bytes] = field(default_factory=list)
    segment_numbers: List[int] = field(default_factory=list)
    is_complete: bool = False

    @property
    def expected_segments(self) -> int:
        """Get expected number of segments (0 if unknown)."""
        return self.total_segments if self.total_segments else 0

    @property
    def received_count(self) -> int:
        """Get number of segments received."""
        return len(self.received_segments)


class SegmentedFrameReassembler:
    """
    Reassembles segmented HDLC frames into complete information fields.

    When an HDLC frame has the segmentation bit set in the format field,
    the information field is split across multiple frames that need to be
    reassembled before processing.
    """

    def __init__(self, max_pending_timeouts: int = 300):
        """
        Initialize the reassembler.

        Args:
            max_pending_timeouts: Maximum time to wait for incomplete segments
        """
        self._pending: Dict[tuple, SegmentedFrameInfo] = {}
        self.max_pending_timeouts = max_pending_timeouts

    def _get_key(self, source_address: int, destination_address: int) -> tuple:
        """Get the key for pending frames dictionary."""
        return (source_address, destination_address)

    def add_segment(
        self,
        source_address: int,
        destination_address: int,
        segment_data: bytes,
        segment_number: int,
        is_last_segment: bool = False,
        total_segments: Optional[int] = None,
    ) -> Optional[bytes]:
        """
        Add a segment and check if reassembly is complete.

        Args:
            source_address: Source logical address
            destination_address: Destination logical address
            segment_data: Segment data (information field without HDLC wrapper)
            segment_number: Segment sequence number
            is_last_segment: Whether this is the last segment
            total_segments: Total number of segments (if known)

        Returns:
            Complete reassembled data if all segments received, None otherwise

        Raises:
            hdlc_exceptions.HdlcParsingError: If segment data is invalid
        """
        key = self._get_key(source_address, destination_address)

        if key not in self._pending:
            self._pending[key] = SegmentedFrameInfo(
                source_address=source_address,
                destination_address=destination_address,
                total_segments=total_segments,
            )

        frame_info = self._pending[key]

        # Check for duplicate segment
        if segment_number in frame_info.segment_numbers:
            LOG.warning(
                f"Duplicate segment {segment_number} received, ignoring",
                source=source_address,
                destination=destination_address,
            )
            return None

        # Add segment
        frame_info.received_segments.append(segment_data)
        frame_info.segment_numbers.append(segment_number)

        # Update total if provided
        if total_segments is not None:
            frame_info.total_segments = total_segments

        # Mark as complete if this is the last segment
        if is_last_segment:
            frame_info.total_segments = segment_number + 1
            frame_info.is_complete = True
        elif frame_info.total_segments is not None:
            # Check if all segments received
            if len(frame_info.received_segments) >= frame_info.total_segments:
                frame_info.is_complete = True

        # Check if reassembly is complete
        if frame_info.is_complete and self._validate_reassembly(frame_info):
            # Reassemble segments in order
            sorted_indices = sorted(range(len(frame_info.received_segments)))
            reassembled = b"".join(
                frame_info.received_segments[i] for i in sorted_indices
            )

            # Clean up
            del self._pending[key]

            LOG.info(
                f"Successfully reassembled {len(frame_info.received_segments)} segments",
                source=source_address,
                destination=destination_address,
                total_bytes=len(reassembled),
            )

            return reassembled

        return None

    def _validate_reassembly(self, frame_info: SegmentedFrameInfo) -> bool:
        """
        Validate that all segments are present and in correct order.

        Args:
            frame_info: Frame information to validate

        Returns:
            True if reassembly can proceed, False otherwise
        """
        expected_count = frame_info.total_segments or len(frame_info.received_segments)

        if len(frame_info.received_segments) != expected_count:
            LOG.warning(
                f"Incomplete reassembly: expected {expected_count}, "
                f"got {len(frame_info.received_segments)} segments",
                source=frame_info.source_address,
                destination=frame_info.destination_address,
            )
            return False

        # Check we have all expected segment numbers
        expected_segments = set(range(expected_count))
        actual_segments = set(frame_info.segment_numbers)

        if expected_segments != actual_segments:
            missing = expected_segments - actual_segments
            LOG.warning(
                f"Missing segments in reassembly: {missing}",
                source=frame_info.source_address,
                destination=frame_info.destination_address,
            )
            return False

        return True

    def cleanup_expired(self) -> int:
        """
        Remove expired pending frame information.

        Returns:
            Number of entries cleaned up
        """
        # In a real implementation, you would track timestamps and remove
        # entries that have been pending too long
        # For now, just return count
        expired_count = len(self._pending)
        self._pending.clear()
        return expired_count

    @property
    def pending_count(self) -> int:
        """Get number of incomplete frame reassemblies pending."""
        return len(self._pending)

    def clear(self) -> None:
        """Clear all pending reassemblies."""
        self._pending.clear()


def split_information_into_segments(
    information: bytes,
    max_info_length: int,
    window_size: int = 1,
) -> List[bytes]:
    """
    Split information field into segments for HDLC transmission.

    Args:
        information: Complete information field data
        max_info_length: Maximum information length per frame (negotiated)
        window_size: Number of frames that can be sent without ACK

    Returns:
        List of information field segments (in transmission order)

    Note:
        The segmentation bit in the HDLC format field should be set
        for all but the last segment when transmitting these segments.
    """
    if len(information) <= max_info_length:
        # No segmentation needed
        return [information]

    segments = []
    offset = 0

    while offset < len(information):
        chunk_size = min(max_info_length, len(information) - offset)
        segments.append(information[offset:offset + chunk_size])
        offset += chunk_size

    return segments


def create_segmented_i_frames(
    destination_address: "HdlcAddress",
    source_address: "HdlcAddress",
    information_segments: List[bytes],
    send_sequence: int,
    receive_sequence: int,
    window_size: int = 1,
) -> List["InformationFrame"]:
    """
    Create a series of I-Frames for segmented transmission.

    This is a helper function for creating I-Frames with proper
    sequence numbers and segmentation bits set.

    Args:
        destination_address: HDLC destination address
        source_address: HDLC source address
        information_segments: List of information segments
        send_sequence: Starting send sequence number
        receive_sequence: Receive sequence number to use
        window_size: Negotiated window size

    Returns:
        List of InformationFrame objects

    Note:
        This is a high-level helper - the actual I-Frame class
        should be imported from dlms_cosem.hdlc.frames.
    """
    from dlms_cosem.hdlc.frames import InformationFrame

    frames = []
    current_ssn = send_sequence

    # Limit number of frames to window size
    frames_to_create = min(len(information_segments), window_size)

    for i in range(frames_to_create):
        segment = information_segments[i]
        is_last = (i == len(information_segments) - 1)
        is_segmented = not is_last

        frame = InformationFrame(
            destination_address=destination_address,
            source_address=source_address,
            payload=segment,
            send_sequence_number=current_ssn,
            receive_sequence_number=receive_sequence,
            segmented=is_segmented,
            final=is_last,
        )

        frames.append(frame)
        current_ssn = (current_ssn + 1) % 8

    return frames
