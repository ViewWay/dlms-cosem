"""Supplementary tests for exception hierarchy."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem.exceptions import (
    DlmsException, DlmsProtocolError, DlmsSecurityError,
    DlmsConnectionError, DlmsClientError, DlmsDataError,
    CommunicationError, TimeoutError, ApduError, ConformanceError,
    DecryptionError, CipheringError, AuthenticationError, HlsError,
    SecuritySuiteError, InvalidSecuritySuiteError, KeyLengthError,
    InvalidSecurityConfigurationError, ApplicationAssociationError,
    DlmsClientException, NoRlrqRlreError, DataParsingError,
    DataValidationError, DlmsErrorCode, ErrorDetail, DetailedDlmsException,
    create_protocol_error, create_security_error, create_connection_error,
    create_timeout_error, create_data_error,
)


class TestExceptionHierarchy:
    def test_dlms_exception_base(self):
        e = DlmsException("test")
        assert str(e) == "test"
        assert e.message == "test"
        assert e.error_code is None

    def test_dlms_exception_with_code(self):
        e = DlmsException("test", error_code=1000)
        assert "[1000]" in str(e)

    def test_protocol_error_inherits(self):
        assert issubclass(DlmsProtocolError, DlmsException)

    def test_security_error_inherits(self):
        assert issubclass(DlmsSecurityError, DlmsException)

    def test_connection_error_inherits(self):
        assert issubclass(DlmsConnectionError, DlmsException)

    def test_client_error_inherits(self):
        assert issubclass(DlmsClientError, DlmsException)

    def test_data_error_inherits(self):
        assert issubclass(DlmsDataError, DlmsException)

    def test_all_exceptions_catchable(self):
        """All custom exceptions should be catchable via DlmsException."""
        exc_types = [
            CommunicationError, TimeoutError, ApduError, ConformanceError,
            DecryptionError, CipheringError, AuthenticationError, HlsError,
            SecuritySuiteError, InvalidSecuritySuiteError, KeyLengthError,
            InvalidSecurityConfigurationError, ApplicationAssociationError,
            NoRlrqRlreError, DataParsingError, DataValidationError,
        ]
        for exc_type in exc_types:
            try:
                raise exc_type("test")
            except DlmsException:
                pass


class TestErrorCodeEnum:
    def test_error_code_values(self):
        assert DlmsErrorCode.PROTOCOL_ERROR == 1000
        assert DlmsErrorCode.SECURITY_ERROR == 2000
        assert DlmsErrorCode.CONNECTION_ERROR == 3000
        assert DlmsErrorCode.CLIENT_ERROR == 4000
        assert DlmsErrorCode.DATA_ERROR == 5000

    def test_all_positive(self):
        for member in DlmsErrorCode:
            assert member.value > 0


class TestErrorDetail:
    def test_creation(self):
        detail = ErrorDetail(code=1000, message="test")
        assert detail.code == 1000
        assert detail.message == "test"
        assert detail.context is None
        assert detail.suggestion is None

    def test_to_dict(self):
        detail = ErrorDetail(code=1000, message="test", context={"key": "val"})
        d = detail.to_dict()
        assert d["code"] == 1000
        assert d["context"]["key"] == "val"


class TestDetailedException:
    def test_creation(self):
        detail = ErrorDetail(code=1000, message="detailed error")
        exc = DetailedDlmsException(detail)
        assert exc.message == "detailed error"
        assert exc.error_code == 1000

    def test_to_dict(self):
        detail = ErrorDetail(code=1000, message="test")
        exc = DetailedDlmsException(detail)
        d = exc.to_dict()
        assert d["code"] == 1000


class TestFactoryFunctions:
    def test_create_protocol_error(self):
        e = create_protocol_error("test", context={"key": "val"})
        assert isinstance(e, DlmsProtocolError)
        assert e.message == "test"

    def test_create_security_error(self):
        e = create_security_error("test", suggestion="try again")
        assert isinstance(e, DlmsSecurityError)

    def test_create_connection_error(self):
        e = create_connection_error("test")
        assert isinstance(e, DlmsConnectionError)

    def test_create_timeout_error(self):
        e = create_timeout_error("timeout", timeout_seconds=30.0)
        assert isinstance(e, TimeoutError)

    def test_create_data_error(self):
        e = create_data_error("parse error")
        assert isinstance(e, DlmsDataError)
