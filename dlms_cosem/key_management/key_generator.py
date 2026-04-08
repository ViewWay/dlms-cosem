"""
Key generation utilities for DLMS/COSEM.

Generates cryptographic keys according to Security Suite specifications.
"""
import os
from dataclasses import dataclass

from dlms_cosem.key_management.security_suite import SecuritySuite
from dlms_cosem.exceptions import InvalidSecuritySuiteError


@dataclass(frozen=True)
class KeyPair:
    """A pair of encryption and authentication keys."""

    encryption_key: bytes
    authentication_key: bytes


class KeyGenerator:
    """
    Generate cryptographic keys according to DLMS/COSEM Security Suite specifications.

    Security Suite 0/1: 16-byte keys (AES-128)
    Security Suite 2: 32-byte keys (AES-256)
    """

    @staticmethod
    def generate_key(suite: int) -> bytes:
        """
        Generate a random encryption key for the specified security suite.

        Args:
            suite: Security suite number (0, 1, or 2)

        Returns:
            Random key bytes of appropriate length

        Raises:
            InvalidSecuritySuiteError: If suite is not valid
        """
        security_suite = SecuritySuite.from_number(suite)
        return os.urandom(security_suite.key_length)

    @staticmethod
    def generate_key_pair(
        suite: int, same_key: bool = True
    ) -> KeyPair:
        """
        Generate an encryption key and authentication key.

        In DLMS/COSEM, the encryption and authentication keys can be the same
        or different depending on the deployment.

        Args:
            suite: Security suite number (0, 1, or 2)
            same_key: If True, use the same key for both (default)

        Returns:
            KeyPair with encryption and authentication keys
        """
        key = KeyGenerator.generate_key(suite)
        if same_key:
            return KeyPair(encryption_key=key, authentication_key=key)

        return KeyPair(
            encryption_key=KeyGenerator.generate_key(suite),
            authentication_key=KeyGenerator.generate_key(suite),
        )

    @staticmethod
    def generate_system_title(manufacturer_id: str = "MDM") -> bytes:
        """
        Generate a DLMS/COSEM system title.

        The system title is 8 bytes:
        - 3 bytes: Manufacturer ID (FLAG ID)
        - 5 bytes: Unique identifier

        Args:
            manufacturer_id: 3-character manufacturer ID

        Returns:
            8-byte system title
        """
        if len(manufacturer_id) < 3:
            manufacturer_id = manufacturer_id.ljust(3, "X")
        unique = os.urandom(5)
        return manufacturer_id[:3].encode("ascii").upper() + unique
