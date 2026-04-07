"""
HDLC Window Control for multi-frame transmission.

This module implements the sliding window mechanism for HDLC I-Frames,
allowing multiple frames to be sent without waiting for acknowledgment.
This improves throughput by reducing round-trip delays.

Window size can be negotiated via HDLC parameter negotiation, with
valid values from 1 (stop-and-wait) to 7 (up to 7 frames unacknowledged).
"""
from dataclasses import dataclass
from typing import List, Set, Optional, Tuple
from enum import IntEnum


class WindowState(IntEnum):
    """States of the sliding window."""
    READY = 0
    SENDING = 1
    WAITING_ACK = 2
    CLOSED = 3


@dataclass
class FrameInfo:
    """
    Information about a single frame in the window.

    Attributes:
        sequence_number: Send sequence number (0-7)
        data: Frame data (without HDLC header/trailer)
        acknowledged: Whether this frame has been acknowledged
        transmitted: Whether this frame has been transmitted
        retransmit_count: Number of retransmission attempts
    """
    sequence_number: int
    data: bytes
    acknowledged: bool = False
    transmitted: bool = False
    retransmit_count: int = 0


class SlidingWindow:
    """
    Sliding window for HDLC I-Frame transmission and reception.

    The window allows multiple frames to be sent without waiting for
    individual acknowledgments, improving throughput.

    Attributes:
        window_size: Maximum number of unacknowledged frames (1-7)
        base_sequence: Sequence number of the oldest unacknowledged frame
        next_sequence: Sequence number for the next frame to send
        receive_sequence: Next expected sequence number from peer
        frames: List of frames in the current window
        state: Current window state
    """

    def __init__(self, window_size: int = 1):
        """
        Initialize the sliding window.

        Args:
            window_size: Maximum window size (1-7)

        Raises:
            ValueError: If window_size is not in valid range
        """
        if not 1 <= window_size <= 7:
            raise ValueError(f"Window size must be 1-7, got {window_size}")

        self.window_size = window_size
        self.base_sequence = 0
        self.next_sequence = 0
        self.receive_sequence = 0
        self.frames: List[Optional[FrameInfo]] = [None] * window_size
        self.state = WindowState.READY

    @property
    def available_slots(self) -> int:
        """Number of available slots for new frames."""
        return self.window_size - self.count_unacknowledged()

    @property
    def window_used(self) -> int:
        """Number of slots currently used in the window."""
        return self.count_unacknowledged()

    def count_unacknowledged(self) -> int:
        """Count frames that have been sent but not yet acknowledged."""
        count = 0
        for i in range(self.window_size):
            seq = (self.base_sequence + i) % 8
            slot = seq % self.window_size
            if self.frames[slot] is not None:
                frame = self.frames[slot]
                if frame is not None and frame.sequence_number >= self.base_sequence and frame.sequence_number < self.base_sequence + 8:
                    if not frame.acknowledged:
                        count += 1
        return count

    def can_send(self) -> bool:
        """Check if a new frame can be sent."""
        return (
            self.state in (WindowState.READY, WindowState.SENDING) and
            self.available_slots > 0
        )

    def add_frame(self, sequence_number: int, data: bytes) -> None:
        """
        Add a frame to the window for transmission.

        Args:
            sequence_number: Send sequence number (0-7)
            data: Frame data

        Raises:
            ValueError: If sequence number is invalid or window is full
        """
        if not 0 <= sequence_number <= 7:
            raise ValueError(f"Sequence number must be 0-7, got {sequence_number}")

        if not self.can_send():
            raise ValueError(f"Cannot send frame, window state={self.state}, available={self.available_slots}")

        slot = sequence_number % self.window_size
        if self.frames[slot] is not None:
            raise ValueError(f"Slot {slot} (seq={sequence_number}) is already occupied")

        self.frames[slot] = FrameInfo(
            sequence_number=sequence_number,
            data=data,
        )
        self.next_sequence = (sequence_number + 1) % 8

    def get_frame_to_transmit(self) -> Optional[Tuple[int, bytes]]:
        """
        Get the next frame that needs to be transmitted.

        Returns:
            Tuple of (sequence_number, frame_data) or None if nothing to send
        """
        for i in range(self.window_size):
            seq = (self.base_sequence + i) % 8
            slot = seq % self.window_size
            frame = self.frames[slot]
            if frame is not None and not frame.transmitted:
                return (seq, frame.data)
        return None

    def mark_transmitted(self, sequence_number: int) -> None:
        """Mark a frame as transmitted."""
        slot = sequence_number % self.window_size
        if self.frames[slot] is not None:
            frame_t = self.frames[slot]
            frame_t.transmitted = True  # type: ignore[union-attr]

    def acknowledge_received(self, receive_sequence: int) -> List[int]:
        """
        Process an acknowledgment (receive sequence number).

        Acknowledges all frames with sequence number less than receive_sequence.

        Args:
            receive_sequence: Receive sequence number from peer

        Returns:
            List of newly acknowledged sequence numbers
        """
        self.receive_sequence = receive_sequence

        newly_acked = []

        # Find all frames that can be acknowledged
        for i in range(self.window_size):
            seq = (self.base_sequence + i) % 8
            slot = seq % self.window_size
            frame = self.frames[slot]

            if frame is None:
                break

            # Check if frame is acknowledged (seq < receive_sequence modulo 8)
            seq_is_acked = self._sequence_less_than(seq, receive_sequence)

            if seq_is_acked and not frame.acknowledged:
                frame.acknowledged = True
                newly_acked.append(seq)
            elif not seq_is_acked:
                # Stop if we hit an unacknowledged frame
                break

        # Slide the window forward
        if newly_acked:
            self._slide_window()

        return newly_acked

    def _sequence_less_than(self, seq1: int, seq2: int) -> bool:
        """
        Compare sequence numbers with wrap-around handling.

        Returns True if seq1 < seq2 (considering wrap-around from 7 to 0).
        """
        if seq2 >= seq1:
            return seq1 < seq2
        else:
            # seq2 wrapped around
            return seq1 >= seq2

    def _slide_window(self) -> None:
        """Slide the window forward, removing acknowledged frames."""
        # Find new base sequence (first unacknowledged frame)
        for i in range(self.window_size):
            seq = (self.base_sequence + i) % 8
            slot = seq % self.window_size
            frame = self.frames[slot]

            if frame is None:
                # Empty slot, nothing to slide
                break

            if not frame.acknowledged:
                # Found first unacknowledged frame
                if i > 0:
                    # Can slide to here
                    self.base_sequence = seq
                    # Clear slots before new base
                    for j in range(i):
                        old_seq = (self.base_sequence + j - i) % 8
                        old_slot = old_seq % self.window_size
                        self.frames[old_slot] = None
                break

        # If window is empty, we can slide further
        all_acked = True
        for i in range(self.window_size):
            slot = i
            frame = self.frames[slot]
            if frame is not None and not frame.acknowledged:
                all_acked = False
                break

        if all_acked:
            # Find the next sequence to use as base
            for i in range(self.window_size):
                slot = i
                if self.frames[slot] is None:
                    # Can move base past this slot
                    old_base = self.base_sequence
                    self.base_sequence = (old_base + i + 1) % 8
                    # Clear cleared slots
                    for j in range(i + 1):
                        self.frames[j] = None
                    break

    def get_unacknowledged_frames(self) -> List[Tuple[int, bytes]]:
        """
        Get all frames that have been transmitted but not yet acknowledged.

        Returns:
            List of (sequence_number, frame_data) tuples
        """
        unacked = []
        for i in range(self.window_size):
            seq = (self.base_sequence + i) % 8
            slot = seq % self.window_size
            frame = self.frames[slot]

            if frame is not None and frame.transmitted and not frame.acknowledged:
                unacked.append((seq, frame.data))

        return unacked

    def reset(self) -> None:
        """Reset the window state."""
        self.base_sequence = 0
        self.next_sequence = 0
        self.receive_sequence = 0
        self.frames = [None] * self.window_size
        self.state = WindowState.READY


class FrameBuffer:
    """
    Buffer for receiving out-of-order frames.

    Stores received frames until they can be delivered in sequence.
    """

    def __init__(self, max_size: int = 256):
        """
        Initialize the frame buffer.

        Args:
            max_size: Maximum number of frames to buffer
        """
        self.max_size = max_size
        self.buffer: dict[int, bytes] = {}
        self.next_expected: int = 0

    def add_frame(self, sequence_number: int, data: bytes) -> bool:
        """
        Add a received frame to the buffer.

        Args:
            sequence_number: Receive sequence number
            data: Frame data

        Returns:
            True if frame was accepted, False if duplicate or buffer full
        """
        if sequence_number in self.buffer:
            # Duplicate frame
            return False

        if len(self.buffer) >= self.max_size:
            # Buffer full
            return False

        self.buffer[sequence_number] = data
        return True

    def get_deliverable_frames(self) -> List[Tuple[int, bytes]]:
        """
        Get all frames that can be delivered in sequence.

        Returns:
            List of (sequence_number, frame_data) tuples in sequence order
        """
        deliverable = []

        while self.next_expected in self.buffer:
            data = self.buffer.pop(self.next_expected)
            deliverable.append((self.next_expected, data))
            self.next_expected = (self.next_expected + 1) % 8

        return deliverable

    def has_frame(self, sequence_number: int) -> bool:
        """Check if a frame is in the buffer."""
        return sequence_number in self.buffer

    @property
    def buffered_count(self) -> int:
        """Number of frames currently buffered."""
        return len(self.buffer)

    def clear(self) -> None:
        """Clear all buffered frames."""
        self.buffer.clear()
        self.next_expected = 0
