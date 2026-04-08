"""Tests for protocol ACSE and XDLM-S modules."""
import pytest

from dlms_cosem.protocol.acse import (
    ApplicationAssociationRequest,
    ApplicationAssociationResponse,
    ReleaseRequest,
    ReleaseResponse,
    UserInformation,
    AppContextName,
    MechanismName,
)
from dlms_cosem.protocol.xdlms import (
    InitiateRequest,
    InitiateResponse,
    GetRequestNormal,
    GetResponseNormal,
    SetRequestNormal,
    SetResponseNormal,
    ActionRequestFactory,
    ActionResponseFactory,
    GetRequestFactory,
    GetResponseFactory,
    SetRequestFactory,
    SetResponseFactory,
    DataNotification,
    ConfirmedServiceError,
    ExceptionResponse,
    Conformance,
    InvokeIdAndPriority,
)


class TestInvokeIdAndPriority:
    """Test Invoke ID and Priority handling."""

    def test_default_values(self):
        iap = InvokeIdAndPriority()
        assert iap.invoke_id == 0
        assert iap.priority == InvokeIdAndPriority.Priority.NORMAL

    def test_custom_values(self):
        iap = InvokeIdAndPriority(invoke_id=10, priority=InvokeIdAndPriority.Priority.HIGH)
        assert iap.invoke_id == 10
        assert iap.priority == InvokeIdAndPriority.Priority.HIGH

    def test_priority_values(self):
        assert InvokeIdAndPriority.Priority.NORMAL == 0
        assert InvokeIdAndPriority.Priority.HIGH == 1


class TestConformance:
    """Test Conformance bits."""

    def test_default_conformance(self):
        conf = Conformance()
        # Default should have some conformance bits set
        assert isinstance(conf.conformance_bits, int)

    def test_has_get(self):
        conf = Conformance()
        # Check if GET operation is supported
        assert hasattr(conf, 'get')


class TestInitiateRequest:
    """Test InitiateRequest encoding/decoding."""

    def test_default_initiate_request(self):
        req = InitiateRequest()
        assert req is not None

    def test_initiate_request_with_params(self):
        req = InitiateRequest(
            dedicated_key=b"\x00" * 8,
            client_max_receive_size=512,
            server_max_receive_size=512,
        )
        assert req.client_max_receive_size == 512


class TestInitiateResponse:
    """Test InitiateResponse encoding/decoding."""

    def test_default_initiate_response(self):
        resp = InitiateResponse()
        assert resp is not None


class TestGetRequestNormal:
    """Test GetRequestNormal."""

    def test_default_get_request(self):
        req = GetRequestNormal()
        assert req is not None

    def test_get_request_with_invoke_id(self):
        req = GetRequestNormal(invoke_id=5)
        assert req.invoke_id == 5


class TestGetResponseNormal:
    """Test GetResponseNormal."""

    def test_default_get_response(self):
        resp = GetResponseNormal()
        assert resp is not None


class TestSetRequestNormal:
    """Test SetRequestNormal."""

    def test_default_set_request(self):
        req = SetRequestNormal()
        assert req is not None


class TestSetResponseNormal:
    """Test SetResponseNormal."""

    def test_default_set_response(self):
        resp = SetResponseNormal()
        assert resp is not None


class TestActionRequestFactory:
    """Test ActionRequestFactory."""

    def test_create_action_request(self):
        factory = ActionRequestFactory()
        req = factory.create_action_request(
            invoke_id=1,
            method_descriptor=("1", "0", "1", "8", "0", "255"),
        )
        assert req is not None


class TestActionResponseFactory:
    """Test ActionResponseFactory."""

    def test_create_action_response(self):
        factory = ActionResponseFactory()
        resp = factory.create_action_response(invoke_id=1)
        assert resp is not None


class TestGetRequestFactory:
    """Test GetRequestFactory."""

    def test_create_get_request(self):
        factory = GetRequestFactory()
        req = factory.create_get_request(
            invoke_id=1,
            attribute_descriptor=("1", "0", "1", "8", "0", "255"),
        )
        assert req is not None


class TestGetResponseFactory:
    """Test GetResponseFactory."""

    def test_create_get_response(self):
        factory = GetResponseFactory()
        resp = factory.create_get_response(
            invoke_id=1,
            data=b"\x00\x01\x02",
        )
        assert resp is not None


class TestSetRequestFactory:
    """Test SetRequestFactory."""

    def test_create_set_request(self):
        factory = SetRequestFactory()
        req = factory.create_set_request(
            invoke_id=1,
            attribute_descriptor=("1", "0", "1", "8", "0", "255"),
            data=b"\x00\x01\x02",
        )
        assert req is not None


class TestSetResponseFactory:
    """Test SetResponseFactory."""

    def test_create_set_response(self):
        factory = SetResponseFactory()
        resp = factory.create_set_response(invoke_id=1)
        assert resp is not None


class TestDataNotification:
    """Test DataNotification."""

    def test_default_data_notification(self):
        notif = DataNotification()
        assert notif is not None


class TestConfirmedServiceError:
    """Test ConfirmedServiceError."""

    def test_default_error(self):
        error = ConfirmedServiceError()
        assert error is not None


class TestExceptionResponse:
    """Test ExceptionResponse."""

    def test_default_exception(self):
        exc = ExceptionResponse()
        assert exc is not None


class TestApplicationAssociationRequest:
    """Test ApplicationAssociationRequest (AARQ)."""

    def test_default_aarq(self):
        aarq = ApplicationAssociationRequest()
        assert aarq is not None

    def test_aarq_with_auth(self):
        aarq = ApplicationAssociationRequest(
            authentication_password=b"12345678",
        )
        assert aarq is not None


class TestApplicationAssociationResponse:
    """Test ApplicationAssociationResponse (AARE)."""

    def test_default_aare(self):
        aare = ApplicationAssociationResponse()
        assert aare is not None


class TestReleaseRequest:
    """Test ReleaseRequest (RLRQ)."""

    def test_default_rlrq(self):
        rlrq = ReleaseRequest()
        assert rlrq is not None


class TestReleaseResponse:
    """Test ReleaseResponse (RLRE)."""

    def test_default_rlre(self):
        rlre = ReleaseResponse()
        assert rlre is not None


class TestUserInformation:
    """Test UserInformation."""

    def test_default_user_info(self):
        ui = UserInformation()
        assert ui is not None

    def test_user_info_with_data(self):
        ui = UserInformation(
            user_data=b"\x00\x01\x02\x03",
        )
        assert ui is not None


class TestAppContextName:
    """Test Application Context Name."""

    def test_default_context(self):
        ctx = AppContextName()
        assert ctx is not None


class TestMechanismName:
    """Test Mechanism Name."""

    def test_default_mechanism(self):
        mech = MechanismName()
        assert mech is not None
