class LocalDlmsProtocolError(Exception):
    """Protocol error"""


class ApplicationAssociationError(Exception):
    """Something went wrong when trying to setup the application association"""


class PreEstablishedAssociationError(Exception):
    """An error when doing illegal things to the connection if it pre established"""


class ConformanceError(Exception):
    """If APDUs does not match connection Conformance"""


class CipheringError(Exception):
    """Something went wrong when ciphering or deciphering an APDU"""


class DlmsClientException(Exception):
    """An exception that is relating to the client"""


class CommunicationError(Exception):
    """Something went wrong in the communication with a meter"""


class CryptographyError(Exception):
    """Something went wrong then applying a cryptographic function"""


class DecryptionError(CryptographyError):
    """
    Unable to decrypt an APDU. It can be due to mismatch in authentication tag
    because the ciphertext has changed or that the key, nonce or associated data is
    wrong
    """


class NoRlrqRlreError(Exception):
    """
    Is raised from connection when a ReleaseRequest is issued on a connection that has use_rlrq_rlre==False
    Control for client to just skip Release and disconnect the lower layer.
    """


# Security Suite Validation Exceptions


class SecuritySuiteError(Exception):
    """Base exception for Security Suite validation errors"""


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
