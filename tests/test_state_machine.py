"""Tests for DLMS connection state machine."""

import pytest

from dlms_cosem import exceptions
from dlms_cosem.state import (
    AWAITING_ACTION_RESPONSE,
    AWAITING_ASSOCIATION_RESPONSE,
    AWAITING_GET_BLOCK_RESPONSE,
    AWAITING_GET_RESPONSE,
    AWAITING_HLS_CLIENT_CHALLENGE_RESULT,
    AWAITING_RELEASE_RESPONSE,
    AWAITING_SET_RESPONSE,
    DlmsConnectionState,
    EndAssociation,
    HLS_DONE,
    HlsFailed,
    HlsStart,
    HlsSuccess,
    NO_ASSOCIATION,
    READY,
    RejectAssociation,
    SHOULD_ACK_LAST_GET_BLOCK,
    SHOULD_SEND_HLS_SEVER_CHALLENGE_RESULT,
)

from dlms_cosem.protocol import acse, xdlms


class TestSentinelStates:
    """Test sentinel state types."""

    def test_sentinel_repr(self):
        assert repr(NO_ASSOCIATION) == "NO_ASSOCIATION"
        assert repr(READY) == "READY"

    def test_sentinel_identity(self):
        assert NO_ASSOCIATION is NO_ASSOCIATION
        assert READY is READY
        assert NO_ASSOCIATION is not READY

    def test_sentinel_type(self):
        assert type(NO_ASSOCIATION) is NO_ASSOCIATION
        assert type(READY) is READY


class TestDlmsConnectionStateInit:
    """Test initial state."""

    def test_default_state(self):
        state = DlmsConnectionState()
        assert state.current_state is NO_ASSOCIATION

    def test_custom_initial_state(self):
        state = DlmsConnectionState(current_state=READY)
        assert state.current_state is READY


class TestAssociationTransitions:
    """Test association state transitions."""

    def test_no_association_to_awaiting_response(self):
        state = DlmsConnectionState()
        event = object.__new__(acse.ApplicationAssociationRequest)
        state.process_event(event)
        assert state.current_state is AWAITING_ASSOCIATION_RESPONSE

    def test_awaiting_response_to_ready(self):
        state = DlmsConnectionState(current_state=AWAITING_ASSOCIATION_RESPONSE)
        event = object.__new__(acse.ApplicationAssociationResponse)
        state.process_event(event)
        assert state.current_state is READY

    def test_awaiting_response_exception_to_no_association(self):
        state = DlmsConnectionState(current_state=AWAITING_ASSOCIATION_RESPONSE)
        event = object.__new__(xdlms.ExceptionResponse)
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION


class TestReleaseTransitions:
    """Test release state transitions."""

    def test_ready_to_awaiting_release(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(acse.ReleaseRequest)
        state.process_event(event)
        assert state.current_state is AWAITING_RELEASE_RESPONSE

    def test_release_response_to_no_association(self):
        state = DlmsConnectionState(current_state=AWAITING_RELEASE_RESPONSE)
        event = object.__new__(acse.ReleaseResponse)
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION

    def test_release_exception_to_ready(self):
        state = DlmsConnectionState(current_state=AWAITING_RELEASE_RESPONSE)
        event = object.__new__(xdlms.ExceptionResponse)
        state.process_event(event)
        assert state.current_state is READY

    def test_end_association(self):
        state = DlmsConnectionState(current_state=READY)
        event = EndAssociation()
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION

    def test_reject_association(self):
        state = DlmsConnectionState(current_state=READY)
        event = RejectAssociation()
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION


class TestGetTransitions:
    """Test GET request state transitions."""

    def test_get_request(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(xdlms.GetRequestNormal)
        state.process_event(event)
        assert state.current_state is AWAITING_GET_RESPONSE

    def test_get_with_list_request(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(xdlms.GetRequestWithList)
        state.process_event(event)
        assert state.current_state is AWAITING_GET_RESPONSE

    def test_get_response_normal(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_RESPONSE)
        event = object.__new__(xdlms.GetResponseNormal)
        state.process_event(event)
        assert state.current_state is READY

    def test_get_response_with_list(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_RESPONSE)
        event = object.__new__(xdlms.GetResponseWithList)
        state.process_event(event)
        assert state.current_state is READY

    def test_get_response_with_block(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_RESPONSE)
        event = object.__new__(xdlms.GetResponseWithBlock)
        state.process_event(event)
        assert state.current_state is SHOULD_ACK_LAST_GET_BLOCK

    def test_get_response_error(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_RESPONSE)
        event = object.__new__(xdlms.GetResponseNormalWithError)
        state.process_event(event)
        assert state.current_state is READY

    def test_get_exception(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_RESPONSE)
        event = object.__new__(xdlms.ExceptionResponse)
        state.process_event(event)
        assert state.current_state is READY


class TestSetTransitions:
    """Test SET request state transitions."""

    def test_set_request(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(xdlms.SetRequestNormal)
        state.process_event(event)
        assert state.current_state is AWAITING_SET_RESPONSE

    def test_set_response(self):
        state = DlmsConnectionState(current_state=AWAITING_SET_RESPONSE)
        event = object.__new__(xdlms.SetResponseNormal)
        state.process_event(event)
        assert state.current_state is READY


class TestActionTransitions:
    """Test ACTION request state transitions."""

    def test_action_request(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(xdlms.ActionRequestNormal)
        state.process_event(event)
        assert state.current_state is AWAITING_ACTION_RESPONSE

    def test_action_response_normal(self):
        state = DlmsConnectionState(current_state=AWAITING_ACTION_RESPONSE)
        event = object.__new__(xdlms.ActionResponseNormal)
        state.process_event(event)
        assert state.current_state is READY

    def test_action_response_with_data(self):
        state = DlmsConnectionState(current_state=AWAITING_ACTION_RESPONSE)
        event = object.__new__(xdlms.ActionResponseNormalWithData)
        state.process_event(event)
        assert state.current_state is READY

    def test_action_response_error(self):
        state = DlmsConnectionState(current_state=AWAITING_ACTION_RESPONSE)
        event = object.__new__(xdlms.ActionResponseNormalWithError)
        state.process_event(event)
        assert state.current_state is READY


class TestHlsTransitions:
    """Test HLS authentication state transitions."""

    def test_hls_start(self):
        state = DlmsConnectionState(current_state=READY)
        event = HlsStart()
        state.process_event(event)
        assert state.current_state is SHOULD_SEND_HLS_SEVER_CHALLENGE_RESULT

    def test_hls_challenge_request(self):
        state = DlmsConnectionState(current_state=SHOULD_SEND_HLS_SEVER_CHALLENGE_RESULT)
        event = object.__new__(xdlms.ActionRequestNormal)
        state.process_event(event)
        assert state.current_state is AWAITING_HLS_CLIENT_CHALLENGE_RESULT

    def test_hls_success(self):
        state = DlmsConnectionState(current_state=AWAITING_HLS_CLIENT_CHALLENGE_RESULT)
        event = object.__new__(xdlms.ActionResponseNormalWithData)
        state.process_event(event)
        assert state.current_state is HLS_DONE

    def test_hls_done_to_ready(self):
        state = DlmsConnectionState(current_state=HLS_DONE)
        event = HlsSuccess()
        state.process_event(event)
        assert state.current_state is READY

    def test_hls_failed(self):
        state = DlmsConnectionState(current_state=AWAITING_HLS_CLIENT_CHALLENGE_RESULT)
        event = object.__new__(xdlms.ActionResponseNormal)
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION

    def test_hls_done_failed(self):
        state = DlmsConnectionState(current_state=HLS_DONE)
        event = HlsFailed()
        state.process_event(event)
        assert state.current_state is NO_ASSOCIATION


class TestBlockTransferTransitions:
    """Test block transfer state transitions."""

    def test_ack_last_block_to_get_block(self):
        state = DlmsConnectionState(current_state=SHOULD_ACK_LAST_GET_BLOCK)
        event = object.__new__(xdlms.GetRequestNext)
        state.process_event(event)
        assert state.current_state is AWAITING_GET_BLOCK_RESPONSE

    def test_get_block_response(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_BLOCK_RESPONSE)
        event = object.__new__(xdlms.GetResponseWithBlock)
        state.process_event(event)
        assert state.current_state is SHOULD_ACK_LAST_GET_BLOCK

    def test_get_block_last(self):
        state = DlmsConnectionState(current_state=AWAITING_GET_BLOCK_RESPONSE)
        event = object.__new__(xdlms.GetResponseLastBlock)
        state.process_event(event)
        assert state.current_state is READY


class TestInvalidTransitions:
    """Test that invalid transitions raise errors."""

    def test_get_request_from_no_association(self):
        state = DlmsConnectionState(current_state=NO_ASSOCIATION)
        event = object.__new__(xdlms.GetRequestNormal)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event(event)

    def test_set_request_from_no_association(self):
        state = DlmsConnectionState(current_state=NO_ASSOCIATION)
        event = object.__new__(xdlms.SetRequestNormal)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event(event)

    def test_action_request_from_no_association(self):
        state = DlmsConnectionState(current_state=NO_ASSOCIATION)
        event = object.__new__(xdlms.ActionRequestNormal)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event(event)

    def test_release_request_from_no_association(self):
        state = DlmsConnectionState(current_state=NO_ASSOCIATION)
        event = object.__new__(acse.ReleaseRequest)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event(event)

    def test_get_request_from_awaiting_set(self):
        state = DlmsConnectionState(current_state=AWAITING_SET_RESPONSE)
        event = object.__new__(xdlms.GetRequestNormal)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event(event)

    def test_unknown_event_type(self):
        state = DlmsConnectionState(current_state=READY)
        with pytest.raises(exceptions.LocalDlmsProtocolError):
            state.process_event("not_a_valid_event")

    def test_error_message_contains_state(self):
        state = DlmsConnectionState(current_state=NO_ASSOCIATION)
        event = object.__new__(xdlms.GetRequestNormal)
        with pytest.raises(exceptions.LocalDlmsProtocolError, match="NO_ASSOCIATION"):
            state.process_event(event)


class TestDataNotification:
    """Test data notification handling."""

    def test_data_notification_stays_ready(self):
        state = DlmsConnectionState(current_state=READY)
        event = object.__new__(xdlms.DataNotification)
        state.process_event(event)
        assert state.current_state is READY


class TestFullLifecycle:
    """Test complete connection lifecycle."""

    def test_connect_get_disconnect(self):
        state = DlmsConnectionState()

        # Connect
        aarq = object.__new__(acse.ApplicationAssociationRequest)
        state.process_event(aarq)
        assert state.current_state is AWAITING_ASSOCIATION_RESPONSE

        aare = object.__new__(acse.ApplicationAssociationResponse)
        state.process_event(aare)
        assert state.current_state is READY

        # GET request
        get_req = object.__new__(xdlms.GetRequestNormal)
        state.process_event(get_req)
        assert state.current_state is AWAITING_GET_RESPONSE

        get_resp = object.__new__(xdlms.GetResponseNormal)
        state.process_event(get_resp)
        assert state.current_state is READY

        # SET request
        set_req = object.__new__(xdlms.SetRequestNormal)
        state.process_event(set_req)
        assert state.current_state is AWAITING_SET_RESPONSE

        set_resp = object.__new__(xdlms.SetResponseNormal)
        state.process_event(set_resp)
        assert state.current_state is READY

        # ACTION request
        act_req = object.__new__(xdlms.ActionRequestNormal)
        state.process_event(act_req)
        assert state.current_state is AWAITING_ACTION_RESPONSE

        act_resp = object.__new__(xdlms.ActionResponseNormal)
        state.process_event(act_resp)
        assert state.current_state is READY

        # Disconnect
        rlrq = object.__new__(acse.ReleaseRequest)
        state.process_event(rlrq)
        assert state.current_state is AWAITING_RELEASE_RESPONSE

        rlre = object.__new__(acse.ReleaseResponse)
        state.process_event(rlre)
        assert state.current_state is NO_ASSOCIATION

    def test_connect_end_association(self):
        state = DlmsConnectionState()

        aarq = object.__new__(acse.ApplicationAssociationRequest)
        state.process_event(aarq)

        aare = object.__new__(acse.ApplicationAssociationResponse)
        state.process_event(aare)

        # Use EndAssociation instead of RLRQ/RLRE
        state.process_event(EndAssociation())
        assert state.current_state is NO_ASSOCIATION

    def test_connect_with_hls(self):
        state = DlmsConnectionState()

        # Association
        aarq = object.__new__(acse.ApplicationAssociationRequest)
        state.process_event(aarq)
        aare = object.__new__(acse.ApplicationAssociationResponse)
        state.process_event(aare)
        assert state.current_state is READY

        # HLS
        state.process_event(HlsStart())
        assert state.current_state is SHOULD_SEND_HLS_SEVER_CHALLENGE_RESULT

        act_req = object.__new__(xdlms.ActionRequestNormal)
        state.process_event(act_req)
        assert state.current_state is AWAITING_HLS_CLIENT_CHALLENGE_RESULT

        act_resp = object.__new__(xdlms.ActionResponseNormalWithData)
        state.process_event(act_resp)
        assert state.current_state is HLS_DONE

        state.process_event(HlsSuccess())
        assert state.current_state is READY
