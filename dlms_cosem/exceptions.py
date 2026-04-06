"""
DLMS/COSEM Exception Hierarchy.

This module defines a unified exception hierarchy for DLMS/COSEM operations,
providing clear categorization and consistent error handling.

Exception Hierarchy:
    DlmsException (base)
    ├── DlmsProtocolError
    │   ├── LocalDlmsProtocolError
    │   ├── ConformanceError
    │   └── ApduError
    ├── DlmsSecurityError
    │   ├── SecuritySuiteError
    │   │   ├── InvalidSecuritySuiteError
    │   │   ├── KeyLengthError
    │   │   └── InvalidSecurityConfigurationError
    │   ├── CryptographyError
    │   │   ├── DecryptionError
    │   │   ├── CipheringError
    │   │   └── HlsError
    │   └── AuthenticationError
    ├── DlmsConnectionError
    │   ├── CommunicationError
    │   ├── TimeoutError
    │   ├── ApplicationAssociationError
    │   └── PreEstablishedAssociationError
    ├── DlmsClientError
    │   └── NoRlrqRlreError
    └── DlmsDataError
        ├── DataParsingError
        └── DataValidationError
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class DlmsException(Exception):
    """
    Base exception for all DLMS/COSEM errors.

    All DLMS/COSEM exceptions should inherit from this class to enable
    broad exception handling and categorization.

    Attributes:
        message: Human-readable error message
        error_code: Optional numeric error code for programmatic handling
        context: Optional dict with additional error context
        suggestion: Optional suggestion for resolving the error
    """

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        self.context: Optional[dict] = None
        self.suggestion: Optional[str] = None
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.error_code is not None:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DlmsProtocolError(DlmsException):
    """
    Base class for DLMS protocol-related errors.

    Raised when there are issues with protocol compliance, APDU encoding/decoding,
    or conformance issues.
    """


class LocalDlmsProtocolError(DlmsProtocolError):
    """Protocol error in the local implementation."""


class ConformanceError(DlmsProtocolError):
    """If APDUs does not match connection Conformance."""


class ApduError(DlmsProtocolError):
    """
    Error in APDU (Application Protocol Data Unit) processing.

    This can occur during encoding, decoding, or validation of APDUs.
    """


class DlmsSecurityError(DlmsException):
    """
    Base class for security-related errors.

    Raised when there are issues with encryption, authentication,
    key management, or security suite configuration.
    """


class CryptographyError(DlmsSecurityError):
    """Something went wrong when applying a cryptographic function."""


class DecryptionError(CryptographyError):
    """
    Unable to decrypt an APDU. It can be due to mismatch in authentication tag
    because the ciphertext has changed or that the key, nonce or associated data is
    wrong
    """


class CipheringError(CryptographyError):
    """Something went wrong when ciphering an APDU."""


class AuthenticationError(DlmsSecurityError):
    """
    Error during authentication process.

    This can occur during HLS (High Level Security) authentication
    or LLS (Low Level Security) authentication.
    """


class HlsError(AuthenticationError):
    """Error in High Level Security authentication."""


class SecuritySuiteError(DlmsSecurityError):
    """Base exception for Security Suite validation errors."""


class InvalidSecuritySuiteError(SecuritySuiteError):
    """
    Raised when an invalid security suite number is provided.

    Valid security suite numbers are 0, 1, or 2 according to DLMS/COSEM
    Yellow Book specification.
    """


class KeyLengthError(SecuritySuiteError):
    """
    Raised when a key has an incorrect length for the specified security suite.

    Security Suite 0: Requires 16-byte keys (AES-128)
    Security Suite 1: Requires 16-byte keys (AES-128)
    Security Suite 2: Requires 32-byte keys (AES-256)
    """


class InvalidSecurityConfigurationError(SecuritySuiteError):
    """
    Raised when the security configuration is invalid or inconsistent.

    This can occur when:
    - Security control fields are inconsistent
    - Required security parameters are missing
    - Authentication and encryption settings conflict
    """


class DlmsConnectionError(DlmsException):
    """
    Base class for connection-related errors.

    Raised when there are issues establishing, maintaining, or
    terminating connections with DLMS devices.
    """


class CommunicationError(DlmsConnectionError):
    """Something went wrong in the communication with a meter."""


class TimeoutError(DlmsConnectionError):
    """
    A operation timed out.

    This can occur when waiting for a response from a meter or when
    a connection attempt times out.
    """


class ApplicationAssociationError(DlmsConnectionError):
    """Something went wrong when trying to setup the application association"""


class PreEstablishedAssociationError(DlmsConnectionError):
    """An error when doing illegal things to the connection if it pre established"""


class DlmsClientError(DlmsException):
    """
    Base class for client-related errors.

    Raised when there are issues with client configuration or operation.
    """


class DlmsClientException(DlmsClientError):
    """
    An exception that is relating to the client.

    Note: Kept for backward compatibility. Prefer using DlmsClientError in new code.
    """


class NoRlrqRlreError(DlmsClientError):
    """
    Is raised from connection when a ReleaseRequest is issued on a connection that has use_rlrq_rlre==False
    Control for client to just skip Release and disconnect the lower layer.
    """


class DlmsDataError(DlmsException):
    """
    Base class for data-related errors.

    Raised when there are issues with data parsing, validation, or encoding.
    """


class DataParsingError(DlmsDataError):
    """
    Error parsing DLMS data.

    This can occur when decoding AXDR/BER encoded data or when
    parsing COSEM object identifiers.
    """


class DataValidationError(DlmsDataError):
    """
    Error validating data.

    This can occur when data fails validation checks, such as
    out-of-range values or incorrect data types.
    """


class DataResultError(DlmsDataError):
    """Error retrieving data from a COSEM attribute."""


class ActionError(DlmsDataError):
    """Error performing a COSEM action/method."""


class HLSError(DlmsException):
    """Error in HLS procedure. Kept for backward compatibility; prefer HlsError."""


# ============================================================================
# Error Code Enumerations
# ============================================================================


class DlmsErrorCode(IntEnum):
    """
    Standard error codes for DLMS/COSEM operations.

    These codes provide programmatic error handling capabilities
    and can be used for automated error response.
    """

    # Protocol errors (1000-1999)
    PROTOCOL_ERROR = 1000
    CONFORMANCE_ERROR = 1001
    APDU_ENCODING_ERROR = 1002
    APDU_DECODING_ERROR = 1003

    # Security errors (2000-2999)
    SECURITY_ERROR = 2000
    INVALID_SECURITY_SUITE = 2001
    KEY_LENGTH_ERROR = 2002
    ENCRYPTION_ERROR = 2003
    DECRYPTION_ERROR = 2004
    AUTHENTICATION_ERROR = 2005
    HLS_AUTHENTICATION_ERROR = 2006

    # Connection errors (3000-3999)
    CONNECTION_ERROR = 3000
    COMMUNICATION_ERROR = 3001
    TIMEOUT_ERROR = 3002
    ASSOCIATION_ERROR = 3003

    # Client errors (4000-4999)
    CLIENT_ERROR = 4000
    CONFIGURATION_ERROR = 4001

    # Data errors (5000-5999)
    DATA_ERROR = 5000
    PARSING_ERROR = 5001
    VALIDATION_ERROR = 5002


# ============================================================================
# Error Data Classes
# ============================================================================


@dataclass
class ErrorDetail:
    """
    Detailed error information for structured error handling.

    Attributes:
        code: Numeric error code from DlmsErrorCode
        message: Human-readable error message
        context: Additional context about the error (e.g., attribute ID, OBIS code)
        suggestion: Optional suggestion for resolving the error
    """

    code: int
    message: str
    context: Optional[dict] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert error detail to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "context": self.context or {},
            "suggestion": self.suggestion,
        }


class DetailedDlmsException(DlmsException):
    """
    Exception with detailed error information.

    This exception type includes structured error details that can be
    used for logging, debugging, or user-facing error messages.

    Attributes:
        detail: Structured error detail
    """

    def __init__(self, detail: ErrorDetail):
        self.detail = detail
        super().__init__(detail.message, detail.code)

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        return self.detail.to_dict()


# ============================================================================
# Convenience Factory Functions
# ============================================================================


def create_protocol_error(
    message: str,
    error_code: int = DlmsErrorCode.PROTOCOL_ERROR,
    context: Optional[dict] = None,
) -> DlmsProtocolError:
    """Create a protocol error with optional context."""
    error = DlmsProtocolError(message, error_code)
    if context:
        error.context = context
    return error


def create_security_error(
    message: str,
    error_code: int = DlmsErrorCode.SECURITY_ERROR,
    context: Optional[dict] = None,
    suggestion: Optional[str] = None,
) -> DlmsSecurityError:
    """Create a security error with optional context and suggestion."""
    error = DlmsSecurityError(message, error_code)
    error.context = context
    error.suggestion = suggestion
    return error


def create_connection_error(
    message: str,
    error_code: int = DlmsErrorCode.CONNECTION_ERROR,
    context: Optional[dict] = None,
) -> DlmsConnectionError:
    """Create a connection error with optional context."""
    error = DlmsConnectionError(message, error_code)
    if context:
        error.context = context
    return error


def create_timeout_error(
    message: str,
    timeout_seconds: Optional[float] = None,
) -> TimeoutError:
    """Create a timeout error with timeout information."""
    context = {"timeout_seconds": timeout_seconds} if timeout_seconds else None
    error = TimeoutError(message, DlmsErrorCode.TIMEOUT_ERROR)
    if context:
        error.context = context
    return error


def create_data_error(
    message: str,
    error_code: int = DlmsErrorCode.DATA_ERROR,
    context: Optional[dict] = None,
) -> DlmsDataError:
    """Create a data error with optional context."""
    error = DlmsDataError(message, error_code)
    if context:
        error.context = context
    return error
