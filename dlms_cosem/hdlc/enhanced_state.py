"""
HDLC Connection State Management with sequence number tracking.

This module enhances the state machine with proper sequence number (SSN/RSN)
management for sliding window operation.
"""
from typing import Any, Optional

import attr
import structlog

from dlms_cosem.hdlc import frames
from dlms_cosem.hdlc.exceptions import LocalProtocolError

LOG = structlog.get_logger()


# Sentinel values for HDLC connection states
class _SentinelBase(type):
    """Base class for sentinel values with identity-based comparison."""
    def __repr__(self):
        return self.__name__


def make_sentinel(name):
    """Create a sentinel value with a nice repr."""
    cls = _SentinelBase(name, (_SentinelBase,), {})
    cls.__class__ = cls
    return cls


NOT_CONNECTED = make_sentinel("NOT_CONNECTED")
IDLE = make_sentinel("IDLE")
AWAITING_RESPONSE = make_sentinel("AWAITING_RESPONSE")
AWAITING_CONNECTION = make_sentinel("AWAITING_CONNECTION")
AWAITING_DISCONNECT = make_sentinel("AWAITING_DISCONNECT")
CLOSED = make_sentinel("CLOSED")


# State transitions for HDLC connection
HDLC_STATE_TRANSITIONS = {
    NOT_CONNECTED: {frames.SetNormalResponseModeFrame: AWAITING_CONNECTION},
    AWAITING_CONNECTION: {frames.UnNumberedAcknowledgmentFrame: IDLE},
    IDLE: {
        frames.InformationFrame: AWAITING_RESPONSE,
        frames.DisconnectFrame: AWAITING_DISCONNECT,
        frames.ReceiveReadyFrame: IDLE,  # RR can be received in IDLE
    },
    AWAITING_RESPONSE: {
        frames.InformationFrame: AWAITING_RESPONSE,  # More data frames
        frames.ReceiveReadyFrame: IDLE,  # ACK received
    },
    AWAITING_DISCONNECT: {frames.UnNumberedAcknowledgmentFrame: NOT_CONNECTED},
}


SEND_STATES = [NOT_CONNECTED, IDLE]
RECEIVE_STATES = [AWAITING_CONNECTION, AWAITING_RESPONSE, AWAITING_DISCONNECT]


@attr.s(auto_attribs=True)
class HdlcConnectionState:
    """
    Enhanced HDLC connection state management with sequence number tracking.

    Attributes:
        current_state: Current connection state
        send_sequence_number: Next send sequence number (SSN, 0-7)
        receive_sequence_number: Next expected receive sequence number (RSN, 0-7)
        window_size: Negotiated window size (1-7, default 1)
        last_received_ssn: Last SSN received from peer
    """

    current_state: Any = attr.ib(default=NOT_CONNECTED)
    send_sequence_number: int = attr.ib(default=0)
    receive_sequence_number: int = attr.ib(default=0)
    window_size: int = attr.ib(default=1)
    last_received_ssn: Optional[int] = attr.ib(default=None)

    def process_frame(self, frame):
        """
        Process an HDLC frame and transition state accordingly.

        Args:
            frame: HDLC frame to process

        Raises:
            LocalProtocolError: If frame is invalid for current state
        """
        frame_type = type(frame)
        self._transition_state(frame_type)

        # Update sequence numbers based on frame type
        if isinstance(frame, frames.InformationFrame):
            # Update last received SSN
            self.last_received_ssn = frame.send_sequence_number
            LOG.debug(f"Received I-Frame with SSN={frame.send_sequence_number}")

        elif isinstance(frame, frames.ReceiveReadyFrame):
            # Update RSN - peer is ready to receive up to this sequence
            self.receive_sequence_number = (frame.receive_sequence_number + 1) % 8
            LOG.debug(f"Received RR with RSN={frame.receive_sequence_number}, "
                      f"next expected={self.receive_sequence_number}")

    def _transition_state(self, frame_type):
        """
        Internal state transition logic.
        """
        try:
            new_state = HDLC_STATE_TRANSITIONS[self.current_state][frame_type]
        except KeyError:
            raise LocalProtocolError(
                f"can't handle frame type {frame_type} when state={self.current_state}"
            )
        old_state = self.current_state
        self.current_state = new_state
        LOG.debug(f"HDLC state transitioned", old_state=old_state, new_state=new_state)

    def increment_send_sequence(self) -> int:
        """
        Increment send sequence number and return the new value.

        Returns:
            New send sequence number (0-7)
        """
        self.send_sequence_number = (self.send_sequence_number + 1) % 8
        return self.send_sequence_number

    def can_send_frame(self) -> bool:
        """
        Check if a new frame can be sent based on window size.

        Returns:
            True if window has space, False otherwise
        """
        if self.current_state not in SEND_STATES:
            return False

        # Calculate how many unacknowledged frames are outstanding
        # This is a simplified check - full implementation would track sent frames
        unacked_frames = 0  # Would be tracked separately

        return unacked_frames < self.window_size

    def reset(self):
        """Reset the connection state to initial values."""
        self.current_state = NOT_CONNECTED
        self.send_sequence_number = 0
        self.receive_sequence_number = 0
        self.last_received_ssn = None

    @property
    def is_connected(self) -> bool:
        """Check if HDLC connection is established."""
        return self.current_state in (IDLE, AWAITING_RESPONSE)
