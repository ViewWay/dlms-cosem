"""
Tests for the DLMS/COSEM exception hierarchy.

Tests for exception structure, error codes, and error details.
"""
import pytest

from dlms_cosem import exceptions
from dlms_cosem.exceptions import (
    ApduError,
    ApplicationAssociationError,
    AuthenticationError,
    ConformanceError,
    create_connection_error,
    create_data_error,
    create_protocol_error,
    create_security_error,
    create_timeout_error,
    DataParsingError,
    DataValidationError,
    DetailedDlmsException,
    DecryptionError,
    DlmsClientError,
    DlmsClientException,
    DlmsConnectionError,
    DlmsDataError,
    DlmsErrorCode,
    DlmsException,
    DlmsProtocolError,
    DlmsSecurityError,
    ErrorDetail,
    HlsError,
    InvalidSecurityConfigurationError,
    InvalidSecuritySuiteError,
    KeyLengthError,
    LocalDlmsProtocolError,
    NoRlrqRlreError,
    PreEstablishedAssociationError,
    SecuritySuiteError,
)

# Use module-level access to avoid conflicts with built-in TimeoutError/CommunicationError
DlmsTimeoutError = exceptions.TimeoutError
DlmsCommunicationError = exceptions.CommunicationError


class TestDlmsException:
    """Tests for the base DlmsException class."""

    def test_create_basic_exception(self):
        """Test creating a basic exception with message."""
        exc = DlmsException("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.error_code is None
        assert str(exc) == "Something went wrong"

    def test_create_exception_with_error_code(self):
        """Test creating an exception with an error code."""
        exc = DlmsException("Error occurred", error_code=1001)
        assert exc.message == "Error occurred"
        assert exc.error_code == 1001
        assert str(exc) == "[1001] Error occurred"


class TestExceptionHierarchy:
    """Tests for the exception hierarchy structure."""

    def test_protocol_exception_inherits_from_base(self):
        """Test DlmsProtocolError inherits from DlmsException."""
        exc = DlmsProtocolError("Protocol error")
        assert isinstance(exc, DlmsException)
        assert isinstance(exc, DlmsProtocolError)

    def test_security_exception_inherits_from_base(self):
        """Test DlmsSecurityError inherits from DlmsException."""
        exc = DlmsSecurityError("Security error")
        assert isinstance(exc, DlmsException)
        assert isinstance(exc, DlmsSecurityError)

    def test_connection_exception_inherits_from_base(self):
        """Test DlmsConnectionError inherits from DlmsException."""
        exc = DlmsConnectionError("Connection error")
        assert isinstance(exc, DlmsException)
        assert isinstance(exc, DlmsConnectionError)

    def test_client_exception_inherits_from_base(self):
        """Test DlmsClientError inherits from DlmsException."""
        exc = DlmsClientError("Client error")
        assert isinstance(exc, DlmsException)
        assert isinstance(exc, DlmsClientError)

    def test_data_exception_inherits_from_base(self):
        """Test DlmsDataError inherits from DlmsException."""
        exc = DlmsDataError("Data error")
        assert isinstance(exc, DlmsException)
        assert isinstance(exc, DlmsDataError)

    def test_specific_exceptions_have_correct_parent(self):
        """Test that specific exceptions have correct parent classes."""
        assert issubclass(LocalDlmsProtocolError, DlmsProtocolError)
        assert issubclass(ConformanceError, DlmsProtocolError)
        assert issubclass(ApduError, DlmsProtocolError)

        assert issubclass(DecryptionError, DlmsSecurityError)
        assert issubclass(AuthenticationError, DlmsSecurityError)
        assert issubclass(HlsError, AuthenticationError)

        assert issubclass(DlmsTimeoutError, DlmsConnectionError)
        assert issubclass(ApplicationAssociationError, DlmsConnectionError)

        assert issubclass(DataParsingError, DlmsDataError)
        assert issubclass(DataValidationError, DlmsDataError)

    def test_security_suite_hierarchy(self):
        """Test SecuritySuite error hierarchy."""
        assert issubclass(SecuritySuiteError, DlmsSecurityError)
        assert issubclass(InvalidSecuritySuiteError, SecuritySuiteError)
        assert issubclass(KeyLengthError, SecuritySuiteError)
        assert issubclass(
            InvalidSecurityConfigurationError, SecuritySuiteError
        )


class TestBackwardCompatibility:
    """Tests for backward compatibility with old exception names."""

    def test_dlms_client_exception_is_alias(self):
        """Test DlmsClientException is an alias for DlmsClientError."""
        exc = DlmsClientException("Client error")
        assert isinstance(exc, DlmsClientError)
        assert isinstance(exc, DlmsException)

    def test_pre_existing_exceptions_still_work(self):
        """Test that pre-existing exceptions still work."""
        # These should all be importable and instantiable
        LocalDlmsProtocolError("Protocol error")
        ApplicationAssociationError("Association error")
        PreEstablishedAssociationError("Pre-established error")
        ConformanceError("Conformance error")
        DecryptionError("Decryption error")
        DlmsCommunicationError("Communication error")  # Use alias to avoid built-in
        NoRlrqRlreError("No RLRQ/RLRE error")


class TestDlmsErrorCode:
    """Tests for DlmsErrorCode enumeration."""

    def test_error_code_ranges(self):
        """Test that error codes are in correct ranges."""
        # Protocol errors: 1000-1999
        assert 1000 <= DlmsErrorCode.PROTOCOL_ERROR < 2000
        assert 1000 <= DlmsErrorCode.CONFORMANCE_ERROR < 2000

        # Security errors: 2000-2999
        assert 2000 <= DlmsErrorCode.SECURITY_ERROR < 3000
        assert 2000 <= DlmsErrorCode.INVALID_SECURITY_SUITE < 3000

        # Connection errors: 3000-3999
        assert 3000 <= DlmsErrorCode.CONNECTION_ERROR < 4000
        assert 3000 <= DlmsErrorCode.TIMEOUT_ERROR < 4000

        # Client errors: 4000-4999
        assert 4000 <= DlmsErrorCode.CLIENT_ERROR < 5000

        # Data errors: 5000-5999
        assert 5000 <= DlmsErrorCode.DATA_ERROR < 6000

    def test_error_code_values_are_unique(self):
        """Test that all error codes have unique values."""
        codes = [e.value for e in DlmsErrorCode]
        assert len(codes) == len(set(codes)), "Error codes must be unique"


class TestErrorDetail:
    """Tests for ErrorDetail dataclass."""

    def test_create_error_detail(self):
        """Test creating an ErrorDetail."""
        detail = ErrorDetail(
            code=1001,
            message="Protocol error occurred",
            context={"operation": "GET"},
            suggestion="Check conformance settings",
        )

        assert detail.code == 1001
        assert detail.message == "Protocol error occurred"
        assert detail.context == {"operation": "GET"}
        assert detail.suggestion == "Check conformance settings"

    def test_error_detail_to_dict(self):
        """Test converting ErrorDetail to dictionary."""
        detail = ErrorDetail(
            code=1001,
            message="Protocol error occurred",
            context={"operation": "GET"},
            suggestion="Check conformance settings",
        )

        result = detail.to_dict()
        assert result == {
            "code": 1001,
            "message": "Protocol error occurred",
            "context": {"operation": "GET"},
            "suggestion": "Check conformance settings",
        }

    def test_error_detail_without_optional_fields(self):
        """Test creating ErrorDetail without optional fields."""
        detail = ErrorDetail(code=1001, message="Protocol error occurred")

        assert detail.code == 1001
        assert detail.message == "Protocol error occurred"
        assert detail.context is None
        assert detail.suggestion is None

    def test_error_detail_to_dict_without_optional_fields(self):
        """Test converting ErrorDetail without optional fields to dict."""
        detail = ErrorDetail(code=1001, message="Protocol error occurred")

        result = detail.to_dict()
        assert result == {
            "code": 1001,
            "message": "Protocol error occurred",
            "context": {},
            "suggestion": None,
        }


class TestDetailedDlmsException:
    """Tests for DetailedDlmsException."""

    def test_create_detailed_exception(self):
        """Test creating a detailed exception."""
        detail = ErrorDetail(
            code=1001,
            message="Protocol error occurred",
            context={"operation": "GET"},
            suggestion="Check conformance settings",
        )

        exc = DetailedDlmsException(detail)

        assert exc.detail == detail
        assert exc.message == "Protocol error occurred"
        assert exc.error_code == 1001
        assert isinstance(exc, DlmsException)

    def test_detailed_exception_to_dict(self):
        """Test converting detailed exception to dictionary."""
        detail = ErrorDetail(
            code=1001,
            message="Protocol error occurred",
            context={"operation": "GET"},
        )

        exc = DetailedDlmsException(detail)
        result = exc.to_dict()

        assert result["code"] == 1001
        assert result["message"] == "Protocol error occurred"
        assert result["context"] == {"operation": "GET"}


class TestFactoryFunctions:
    """Tests for exception factory functions."""

    def test_create_protocol_error_basic(self):
        """Test creating a protocol error."""
        exc = create_protocol_error("Protocol error")
        assert isinstance(exc, DlmsProtocolError)
        assert exc.message == "Protocol error"
        assert exc.error_code == DlmsErrorCode.PROTOCOL_ERROR

    def test_create_protocol_error_with_context(self):
        """Test creating a protocol error with context."""
        exc = create_protocol_error(
            "Protocol error", context={"operation": "GET"}
        )
        assert exc.context == {"operation": "GET"}

    def test_create_security_error_basic(self):
        """Test creating a security error."""
        exc = create_security_error("Security error")
        assert isinstance(exc, DlmsSecurityError)
        assert exc.message == "Security error"
        assert exc.error_code == DlmsErrorCode.SECURITY_ERROR

    def test_create_security_error_with_suggestion(self):
        """Test creating a security error with suggestion."""
        exc = create_security_error(
            "Security error", suggestion="Check encryption keys"
        )
        assert exc.suggestion == "Check encryption keys"

    def test_create_connection_error_basic(self):
        """Test creating a connection error."""
        exc = create_connection_error("Connection error")
        assert isinstance(exc, DlmsConnectionError)
        assert exc.message == "Connection error"
        assert exc.error_code == DlmsErrorCode.CONNECTION_ERROR

    def test_create_timeout_error_basic(self):
        """Test creating a timeout error."""
        exc = create_timeout_error("Operation timed out")
        assert isinstance(exc, DlmsTimeoutError)
        assert exc.message == "Operation timed out"
        assert exc.error_code == DlmsErrorCode.TIMEOUT_ERROR

    def test_create_timeout_error_with_timeout(self):
        """Test creating a timeout error with timeout information."""
        exc = create_timeout_error("Operation timed out", timeout_seconds=30.0)
        assert exc.context == {"timeout_seconds": 30.0}

    def test_create_data_error_basic(self):
        """Test creating a data error."""
        exc = create_data_error("Data error")
        assert isinstance(exc, DlmsDataError)
        assert exc.message == "Data error"
        assert exc.error_code == DlmsErrorCode.DATA_ERROR


class TestExceptionCatching:
    """Tests for exception catching patterns."""

    def test_catch_base_exception(self):
        """Test catching all DLMS exceptions via base class."""
        exceptions = [
            DlmsProtocolError("Protocol error"),
            DlmsSecurityError("Security error"),
            DlmsConnectionError("Connection error"),
            DlmsClientError("Client error"),
            DlmsDataError("Data error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, DlmsException)

    def test_catch_specific_protocol_errors(self):
        """Test catching specific protocol errors."""
        exceptions = [
            LocalDlmsProtocolError("Local error"),
            ConformanceError("Conformance error"),
            ApduError("APDU error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, DlmsProtocolError)

    def test_catch_specific_security_errors(self):
        """Test catching specific security errors."""
        exceptions = [
            DecryptionError("Decryption error"),
            AuthenticationError("Auth error"),
            HlsError("HLS error"),
            InvalidSecuritySuiteError("Invalid suite"),
            KeyLengthError("Key length"),
        ]

        for exc in exceptions:
            assert isinstance(exc, DlmsSecurityError)

    def test_catch_specific_connection_errors(self):
        """Test catching specific connection errors."""
        exceptions = [
            DlmsTimeoutError("Timeout"),
            ApplicationAssociationError("Association error"),
            DlmsCommunicationError("Communication error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, DlmsConnectionError)
