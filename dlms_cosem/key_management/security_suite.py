"""
DLMS/COSEM Security Suite definitions.

This module provides the SecuritySuite class and related enums for managing
security suite configurations according to DLMS UA 1000-5 Ed. 3.
"""
from dataclasses import dataclass
from enum import IntEnum

from dlms_cosem.exceptions import InvalidSecuritySuiteError, KeyLengthError


class SecuritySuiteNumber(IntEnum):
    """
    DLMS/COSEM Security Suite numbers as defined in the DLMS UA Yellow Book.

    Each security suite defines the cryptographic algorithms and key sizes to be used.
    """

    SUITE_0 = 0
    """AES-128-GCM with 16-byte keys (128 bits)"""

    SUITE_1 = 1
    """AES-128-GCM with 16-byte keys (128 bits) - Same as Suite 0"""

    SUITE_2 = 2
    """AES-256-GCM with 32-byte keys (256 bits)"""


@dataclass(frozen=True)
class SecuritySuite:
    """
    Represents a DLMS/COSEM Security Suite with its configuration requirements.

    Attributes:
        number: Security suite number (0, 1, or 2)
        key_length: Required key length in bytes (16 for Suite 0/1, 32 for Suite 2)
        algorithm: Cryptographic algorithm name
        key_bits: Key length in bits for display purposes
    """

    number: int
    key_length: int
    algorithm: str
    key_bits: int

    @classmethod
    def from_number(cls, suite_number: int) -> "SecuritySuite":
        """
        Get a SecuritySuite instance from its number.

        Raises:
            InvalidSecuritySuiteError: If suite_number is not 0, 1, or 2
        """
        try:
            return _SECURITY_SUITES[suite_number]
        except KeyError:
            valid_suites = ", ".join(str(n) for n in _SECURITY_SUITES.keys())
            raise InvalidSecuritySuiteError(
                f"Invalid security suite number: {suite_number}. "
                f"Valid security suites are: {valid_suites}"
            )

    def validate_key(self, key: bytes, key_name: str = "key") -> None:
        """
        Validate that a key has the correct length for this security suite.

        Args:
            key: The key bytes to validate
            key_name: Name of the key for error messages (e.g., "encryption key", "auth key")

        Raises:
            KeyLengthError: If the key length is incorrect
        """
        if len(key) != self.key_length:
            raise KeyLengthError(
                f"{key_name} length is {len(key)} bytes, but "
                f"Security Suite {self.number} ({self.algorithm}) requires "
                f"{self.key_length} bytes ({self.key_bits} bits). "
                f"Got: {key.hex()[:32]}{'...' if len(key) > 16 else ''}"
            )

    def __str__(self) -> str:
        return f"Security Suite {self.number} ({self.algorithm}, {self.key_bits}-bit)"


# Security suite definitions according to DLMS UA 1000-5 Ed. 3
_SECURITY_SUITES: dict[int, SecuritySuite] = {
    0: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_0,
        key_length=16,
        algorithm="AES-128-GCM",
        key_bits=128,
    ),
    1: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_1,
        key_length=16,
        algorithm="AES-128-GCM",
        key_bits=128,
    ),
    2: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_2,
        key_length=32,
        algorithm="AES-256-GCM",
        key_bits=256,
    ),
}
