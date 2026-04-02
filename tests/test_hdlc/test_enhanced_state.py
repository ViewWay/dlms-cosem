"""
Tests for HDLC enhanced connection state management module.
"""
import pytest

from dlms_cosem.hdlc.enhanced_state import (
    HdlcConnectionState,
    NOT_CONNECTED,
    IDLE,
    AWAITING_RESPONSE,
    AWAITING_CONNECTION,
    AWAITING_DISCONNECT,
    CLOSED,
    HDLC_STATE_TRANSITIONS,
    SEND_STATES,
    RECEIVE_STATES,
)
from dlms_cosem.hdlc import frames


class TestSentinelValues:
    """Tests for the sentinel state values."""

    def test_not_connected_repr(self):
        """Test NOT_CONNECTED sentinel representation."""
        assert repr(NOT_CONNECTED) == "NOT_CONNECTED"

    def test_idle_repr(self):
        """Test IDLE sentinel representation."""
        assert repr(IDLE) == "IDLE"

    def test_awaiting_response_repr(self):
        """Test AWAITING_RESPONSE sentinel representation."""
        assert repr(AWAITING_RESPONSE) == "AWAITING_RESPONSE"

    def test_sentinel_identity_comparison(self):
        """Test that sentinel values use identity comparison."""
        assert NOT_CONNECTED is NOT_CONNECTED
        assert IDLE is IDLE


class TestStateTransitions:
    """Tests for the HDLC state transition table."""

    def test_transitions_from_not_connected(self):
        """Test valid transitions from NOT_CONNECTED state."""
        transitions = HDLC_STATE_TRANSITIONS[NOT_CONNECTED]
        assert frames.SetNormalResponseModeFrame in transitions
        assert transitions[frames.SetNormalResponseModeFrame] == AWAITING_CONNECTION

    def test_transitions_from_awaiting_connection(self):
        """Test valid transitions from AWAITING_CONNECTION state."""
        transitions = HDLC_STATE_TRANSITIONS[AWAITING_CONNECTION]
        assert frames.UnNumberedAcknowledgmentFrame in transitions
        assert transitions[frames.UnNumberedAcknowledgmentFrame] == IDLE

    def test_transitions_from_idle(self):
        """Test valid transitions from IDLE state."""
        transitions = HDLC_STATE_TRANSITIONS[IDLE]
        assert frames.InformationFrame in transitions
        assert frames.DisconnectFrame in transitions
        assert frames.ReceiveReadyFrame in transitions

    def test_transitions_from_awaiting_response(self):
        """Test valid transitions from AWAITING_RESPONSE state."""
        transitions = HDLC_STATE_TRANSITIONS[AWAITING_RESPONSE]
        assert frames.InformationFrame in transitions
        assert frames.ReceiveReadyFrame in transitions


class TestHdlcConnectionState:
    """Tests for the HdlcConnectionState class."""

    def test_init_default(self):
        """Test initialization with default values."""
        state = HdlcConnectionState()
        assert state.current_state == NOT_CONNECTED
        assert state.send_sequence_number == 0
        assert state.receive_sequence_number == 0
        assert state.window_size == 1
        assert state.last_received_ssn is None

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        state = HdlcConnectionState(
            send_sequence_number=3,
            receive_sequence_number=5,
            window_size=4,
        )
        assert state.send_sequence_number == 3
        assert state.receive_sequence_number == 5
        assert state.window_size == 4

    def test_init_with_last_received_ssn(self):
        """Test initialization with last_received_ssn."""
        state = HdlcConnectionState(last_received_ssn=2)
        assert state.last_received_ssn == 2

    def test_process_frame_snrm(self):
        """Test processing SNRM frame."""
        state = HdlcConnectionState()
        snrm = frames.SetNormalResponseModeFrame(
            destination_address=frames.HdlcAddress(0, None),
            source_address=frames.HdlcAddress(1, None),
        )
        state.process_frame(snrm)
        assert state.current_state == AWAITING_CONNECTION

    def test_process_frame_ua_when_awaiting_connection(self):
        """Test processing UA frame when awaiting connection."""
        state = HdlcConnectionState()
        state.current_state = AWAITING_CONNECTION

        ua = frames.UnNumberedAcknowledgmentFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
        )
        state.process_frame(ua)
        assert state.current_state == IDLE

    def test_process_frame_information_when_idle(self):
        """Test processing Information frame when idle."""
        state = HdlcConnectionState()
        state.current_state = IDLE

        info = frames.InformationFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
            payload=b"data",
            send_sequence_number=0,
            receive_sequence_number=0,
        )
        state.process_frame(info)
        assert state.current_state == AWAITING_RESPONSE
        assert state.last_received_ssn == 0

    def test_process_frame_rr_when_awaiting_response(self):
        """Test processing RR frame when awaiting response."""
        state = HdlcConnectionState()
        state.current_state = AWAITING_RESPONSE
        state.receive_sequence_number = 0

        rr = frames.ReceiveReadyFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
            receive_sequence_number=2,
        )
        state.process_frame(rr)
        assert state.current_state == IDLE
        assert state.receive_sequence_number == 3  # (2 + 1) % 8

    def test_process_frame_invalid_transition(self):
        """Test that invalid transitions raise an error."""
        from dlms_cosem.hdlc.exceptions import LocalProtocolError

        state = HdlcConnectionState()
        state.current_state = AWAITING_CONNECTION

        # DISC is not valid from AWAITING_CONNECTION
        disc = frames.DisconnectFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
        )

        with pytest.raises(LocalProtocolError):
            state.process_frame(disc)

    def test_increment_send_sequence(self):
        """Test incrementing send sequence number."""
        state = HdlcConnectionState()
        assert state.send_sequence_number == 0

        new_ssn = state.increment_send_sequence()
        assert new_ssn == 1
        assert state.send_sequence_number == 1

    def test_increment_send_sequence_wraps_at_7(self):
        """Test that send sequence number wraps from 7 to 0."""
        state = HdlcConnectionState(send_sequence_number=7)
        new_ssn = state.increment_send_sequence()
        assert new_ssn == 0

    def test_can_send_frame_when_idle(self):
        """Test can_send_frame returns True when IDLE."""
        state = HdlcConnectionState()
        state.current_state = IDLE
        assert state.can_send_frame() is True

    def test_can_send_frame_when_not_connected(self):
        """Test can_send_frame returns True when NOT_CONNECTED."""
        state = HdlcConnectionState()
        assert state.can_send_frame() is True

    def test_cannot_send_frame_when_awaiting_response(self):
        """Test can_send_frame returns False when AWAITING_RESPONSE."""
        state = HdlcConnectionState()
        state.current_state = AWAITING_RESPONSE
        assert state.can_send_frame() is False

    def test_cannot_send_frame_when_disconnected(self):
        """Test can_send_frame returns False when CLOSED."""
        state = HdlcConnectionState()
        state.current_state = CLOSED
        assert state.can_send_frame() is False

    def test_is_connected_property(self):
        """Test the is_connected property."""
        state = HdlcConnectionState()

        # Not connected initially
        assert state.is_connected is False

        # Connected when IDLE
        state.current_state = IDLE
        assert state.is_connected is True

        # Connected when AWAITING_RESPONSE
        state.current_state = AWAITING_RESPONSE
        assert state.is_connected is True

        # Not connected when AWAITING_CONNECTION
        state.current_state = AWAITING_CONNECTION
        assert state.is_connected is False

    def test_reset(self):
        """Test resetting the connection state."""
        state = HdlcConnectionState()
        state.current_state = IDLE
        state.send_sequence_number = 5
        state.receive_sequence_number = 3
        state.last_received_ssn = 4

        state.reset()

        assert state.current_state == NOT_CONNECTED
        assert state.send_sequence_number == 0
        assert state.receive_sequence_number == 0
        assert state.last_received_ssn is None

    def test_process_disconnect_frame(self):
        """Test processing DISC frame."""
        state = HdlcConnectionState()
        state.current_state = IDLE

        disc = frames.DisconnectFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
        )
        state.process_frame(disc)
        assert state.current_state == AWAITING_DISCONNECT

    def test_process_ua_when_awaiting_disconnect(self):
        """Test processing UA frame when awaiting disconnect."""
        state = HdlcConnectionState()
        state.current_state = AWAITING_DISCONNECT

        ua = frames.UnNumberedAcknowledgmentFrame(
            destination_address=frames.HdlcAddress(1, None),
            source_address=frames.HdlcAddress(0, None),
        )
        state.process_frame(ua)
        assert state.current_state == NOT_CONNECTED


class TestSendReceiveStates:
    """Tests for the SEND_STATES and RECEIVE_STATES constants."""

    def test_send_states_contains_valid_states(self):
        """Test that SEND_STATES contains correct states."""
        assert NOT_CONNECTED in SEND_STATES
        assert IDLE in SEND_STATES
        assert AWAITING_RESPONSE not in SEND_STATES

    def test_receive_states_contains_valid_states(self):
        """Test that RECEIVE_STATES contains correct states."""
        assert AWAITING_CONNECTION in RECEIVE_STATES
        assert AWAITING_RESPONSE in RECEIVE_STATES
        assert AWAITING_DISCONNECT in RECEIVE_STATES
        assert IDLE not in RECEIVE_STATES
