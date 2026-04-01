"""
Security profile management for DLMS/COSEM.

Defines SecurityProfile dataclass and predefined security strategies.
"""
from dataclasses import dataclass

from dlms_cosem.enumerations import AuthenticationMechanism
from dlms_cosem.exceptions import KeyLengthError, InvalidSecuritySuiteError
from dlms_cosem.key_management.formatters import KeyFormatter
from dlms_cosem.key_management.security_suite import SecuritySuite


@dataclass
class SecurityProfile:
    """
    A complete DLMS/COSEM security configuration.

    Attributes:
        name: Profile identifier (e.g., "default", "meter1")
        suite: Security suite number (0, 1, or 2)
        encryption_key: Encryption key bytes
        authentication_key: Authentication key bytes
        system_title: 8-byte system title
        authentication_method: Authentication mechanism to use
        authenticated: Whether to use authentication
        encrypted: Whether to use encryption
    """

    name: str
    suite: int
    encryption_key: bytes
    authentication_key: bytes
    system_title: bytes = b""
    authentication_method: AuthenticationMechanism = AuthenticationMechanism.HLS_GMAC
    authenticated: bool = True
    encrypted: bool = True

    def validate(self) -> None:
        """
        Validate the security profile.

        Raises:
            InvalidSecuritySuiteError: If suite number is invalid
            KeyLengthError: If key lengths don't match suite requirements
        """
        suite_info = SecuritySuite.from_number(self.suite)
        suite_info.validate_key(self.encryption_key, "encryption_key")
        suite_info.validate_key(self.authentication_key, "authentication_key")

    def to_dict(self, include_secrets: bool = False) -> dict:
        """
        Convert profile to dictionary.

        Args:
            include_secrets: Whether to include actual key values

        Returns:
            Dictionary representation
        """
        data = {
            "name": self.name,
            "suite": self.suite,
            "system_title": self.system_title.hex() if self.system_title else "",
            "authentication_method": self.authentication_method.name,
            "authenticated": self.authenticated,
            "encrypted": self.encrypted,
        }

        if include_secrets:
            data["encryption_key"] = KeyFormatter.format_key(self.encryption_key, "hex")
            data["authentication_key"] = KeyFormatter.format_key(
                self.authentication_key, "hex"
            )
        else:
            data["encryption_key"] = "***"
            data["authentication_key"] = "***"

        return data


# Predefined security strategies for common use cases
SECURITY_STRATEGIES: dict[str, SecurityProfile] = {
    "none": SecurityProfile(
        name="none",
        suite=0,
        encryption_key=b"",
        authentication_key=b"",
        authentication_method=AuthenticationMechanism.NONE,
        authenticated=False,
        encrypted=False,
    ),
    "lls": SecurityProfile(
        name="lls",
        suite=0,
        encryption_key=b"",
        authentication_key=b"",  # Will be set by user
        authentication_method=AuthenticationMechanism.LLS,
        authenticated=True,
        encrypted=False,
    ),
    "hls-gmac": SecurityProfile(
        name="hls-gmac",
        suite=0,
        encryption_key=b"",  # Will be set by user
        authentication_key=b"",  # Will be set by user
        authentication_method=AuthenticationMechanism.HLS_GMAC,
        authenticated=True,
        encrypted=True,
    ),
    "hls-suite2": SecurityProfile(
        name="hls-suite2",
        suite=2,
        encryption_key=b"",  # Will be set by user (32 bytes)
        authentication_key=b"",  # Will be set by user (32 bytes)
        authentication_method=AuthenticationMechanism.HLS_GMAC,
        authenticated=True,
        encrypted=True,
    ),
}
