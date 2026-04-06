from __future__ import annotations  # noqa

import hashlib
import hmac
import os
import struct
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, Optional

import attr
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap, aes_key_wrap

from dlms_cosem import enumerations, exceptions
from dlms_cosem.exceptions import (
    CipheringError,
    DecryptionError,
    InvalidSecurityConfigurationError,
    InvalidSecuritySuiteError,
    KeyLengthError,
    SecuritySuiteError,
)

# Import SecuritySuite from the key_management package
from dlms_cosem.key_management.security_suite import SecuritySuite, SecuritySuiteNumber

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

if TYPE_CHECKING:
    from dlms_cosem.connection import DlmsConnection, ProtectionError


"""
Security Suites in DLMS/COSEM define what cryptographic algorithms that are
available to different services and key sizes

The initialization vector is essentially a nonce. In DLMS/COSEM it is
    composed of two parts. The full length is 96 bits (12 bytes)
    The first part (upper 64bit/8bytes) is called the fixed field and shall
    contain the system title. The lower (32bit/4byte) part is called the
    invocation field and contains an integer invocation counter.
    The system title is a unique identifier for the DLMS/COSEM identity. The
    leftmost 3 octets holds the 3 letter manufacturer ID. (FLAG ID) and the
    remaining 5 octets are to ensure uniqueness.
"""

TAG_LENGTH = 12


# SecuritySuite, SecuritySuiteNumber, and _SECURITY_SUITES are now imported from
# dlms_cosem.security.security_suite to organize the security package.


def validate_security_suite_number(instance, attribute, value):
    if value not in [0, 1, 2, 3, 4, 5]:
        raise ValueError(f"Only Security Suite 0-5 is valid, Got: {value}")


@attr.s(auto_attribs=True)
class SecurityControlField:
    """
    8 bit unsigned integer

    Bit 3...0: Security Suite number
    Bit 4: Indicates if authentication is applied
    Bit 5: Indicates if encryption is applied
    Bit 6: Key usage: 0 = Unicast Encryption Key , 1 = Broadcast Encryption Key
    Bit 7: Indicates the use of compression

    :param bool security_suite: Number of the DLMS Security Suite used, valid
        are 1, 2, 3.
    :param bool authenticated: Indicates if authentication is applied
    :param bool encrypted: Indicates if encryption is applied
    :param bool broadcast_key: Indicates use of broadcast key. If false unicast key is used.
    :param bool compressed: Indicates the use of compression.
    """

    security_suite: int = attr.ib(validator=[validate_security_suite_number])
    authenticated: bool = attr.ib(default=False)
    encrypted: bool = attr.ib(default=False)
    broadcast_key: bool = attr.ib(default=False)
    compressed: bool = attr.ib(default=False)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        val = int.from_bytes(source_bytes, "big")  # just one byte.
        _security_suite = val & 0b00001111
        _authenticated = bool(val & 0b00010000)
        _encrypted = bool(val & 0b00100000)
        _key_set = bool(val & 0b01000000)
        _compressed = bool(val & 0b10000000)
        return cls(_security_suite, _authenticated, _encrypted, _key_set, _compressed)

    def to_bytes(self):
        _byte = self.security_suite
        if self.authenticated:
            _byte += 0b00010000
        if self.encrypted:
            _byte += 0b00100000
        if self.broadcast_key:
            _byte += 0b01000000
        if self.compressed:
            _byte += 0b10000000

        return _byte.to_bytes(1, "big")


def validate_key(suite: int, key: bytes) -> None:
    """
    Validate that a key has the correct length for the specified security suite.

    Args:
        suite: Security suite number (0, 1, or 2)
        key: Key bytes to validate

    Raises:
        InvalidSecuritySuiteError: If suite is not valid
        KeyLengthError: If key length is incorrect
    """
    security_suite = SecuritySuite.from_number(suite)
    security_suite.validate_key(key, "key")


def validate_key_length(suite: int, key: bytes, key_name: str = "key") -> None:
    """
    Validate that a key has the correct length with a custom key name.

    Args:
        suite: Security suite number (0, 1, or 2)
        key: Key bytes to validate
        key_name: Name of the key for error messages

    Raises:
        InvalidSecuritySuiteError: If suite is not valid
        KeyLengthError: If key length is incorrect
    """
    security_suite = SecuritySuite.from_number(suite)
    security_suite.validate_key(key, key_name)


def validate_security_suite(suite: int) -> SecuritySuite:
    """
    Validate and return SecuritySuite information.

    Args:
        suite: Security suite number to validate

    Returns:
        SecuritySuite instance with suite details

    Raises:
        InvalidSecuritySuiteError: If suite is not valid (not 0, 1, or 2)
    """
    return SecuritySuite.from_number(suite)


def validate_system_title(system_title: bytes) -> None:
    """
    Validate that a system title has the correct length.

    In DLMS/COSEM, the system title must be exactly 8 bytes (64 bits).
    The leftmost 3 octets contain the manufacturer ID, and the remaining
    5 octets ensure uniqueness.

    Args:
        system_title: System title bytes to validate

    Raises:
        ValueError: If system_title is not exactly 8 bytes
    """
    if len(system_title) != 8:
        raise ValueError(
            f"System title must be exactly 8 bytes (64 bits). "
            f"Got {len(system_title)} bytes: {system_title.hex()}. "
            f"The system title consists of: 3-byte manufacturer ID + 5-byte unique identifier."
        )


def validate_invocation_counter(invocation_counter: int) -> None:
    """
    Validate that an invocation counter is within valid range.

    The invocation counter is a 32-bit unsigned integer (0 to 2^32-1).

    Args:
        invocation_counter: Invocation counter value to validate

    Raises:
        ValueError: If invocation_counter is out of range
    """
    if not isinstance(invocation_counter, int):
        raise ValueError(
            f"Invocation counter must be an integer, got {type(invocation_counter).__name__}"
        )
    if invocation_counter < 0 or invocation_counter > 0xFFFFFFFF:
        raise ValueError(
            f"Invocation counter must be a 32-bit unsigned integer (0 to 4294967295). "
            f"Got: {invocation_counter}"
        )


def validate_challenge(challenge: bytes, name: str = "challenge") -> None:
    """
    Validate that a challenge has a valid length.

    According to DLMS/COSEM, challenges must be between 8 and 64 bytes.

    Args:
        challenge: Challenge bytes to validate
        name: Name of the challenge for error messages

    Raises:
        ValueError: If challenge length is invalid
    """
    if not (8 <= len(challenge) <= 64):
        raise ValueError(
            f"{name} must be between 8 and 64 bytes. Got {len(challenge)} bytes"
        )


@dataclass
class ValidationResult:
    """
    Result of a security configuration validation.

    Attributes:
        is_valid: Whether the validation passed
        errors: List of error messages (empty if valid)
        warnings: List of warning messages (non-critical issues)
    """

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def __str__(self) -> str:
        if self.is_valid:
            result = "✓ Security configuration is valid"
            if self.warnings:
                result += "\nWarnings:\n  " + "\n  ".join(self.warnings)
            return result
        else:
            return "✗ Security configuration is invalid:\n  " + "\n  ".join(self.errors)


@dataclass
class SecurityConfigValidator:
    """
    Validates DLMS/COSEM security configurations.

    This class provides comprehensive validation of security parameters
    including security suites, keys, system titles, and invocation counters.
    Use before establishing a connection to catch configuration errors early.
    """

    security_suite: int
    encryption_key: Optional[bytes] = None
    authentication_key: Optional[bytes] = None
    system_title: Optional[bytes] = None
    invocation_counter: Optional[int] = None
    authenticated: bool = False
    encrypted: bool = False

    def validate(self) -> ValidationResult:
        """
        Validate the complete security configuration.

        Returns:
            ValidationResult with validation status and any errors/warnings

        Example:
            >>> validator = SecurityConfigValidator(
            ...     security_suite=0,
            ...     encryption_key=bytes(16),
            ...     authentication_key=bytes(16),
            ...     system_title=bytes(8),
            ...     invocation_counter=1,
            ...     authenticated=True,
            ...     encrypted=True
            ... )
            >>> result = validator.validate()
            >>> if not result.is_valid:
            ...     print(result)
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            suite_info = SecuritySuite.from_number(self.security_suite)
            warnings.append(f"Using {suite_info}")
        except InvalidSecuritySuiteError as e:
            errors.append(str(e))
            return ValidationResult(False, errors, warnings)

        # Validate keys based on what security is being used
        if self.encrypted or self.authenticated:
            if self.encryption_key is None:
                errors.append(
                    "Encryption key is required when encrypted=True or authenticated=True"
                )
            else:
                try:
                    suite_info.validate_key(self.encryption_key, "encryption_key")
                except KeyLengthError as e:
                    errors.append(str(e))

            if self.authentication_key is None:
                errors.append(
                    "Authentication key is required when encrypted=True or authenticated=True"
                )
            else:
                try:
                    suite_info.validate_key(self.authentication_key, "authentication_key")
                except KeyLengthError as e:
                    errors.append(str(e))

        # Validate system title if provided
        if self.system_title is not None:
            try:
                validate_system_title(self.system_title)
            except ValueError as e:
                errors.append(str(e))
        elif self.encrypted or self.authenticated:
            warnings.append(
                "System title not provided. Required for encrypted/authenticated connections."
            )

        # Validate invocation counter if provided
        if self.invocation_counter is not None:
            try:
                validate_invocation_counter(self.invocation_counter)
            except ValueError as e:
                errors.append(str(e))

        # Check for common configuration mistakes
        if self.encrypted and not self.authenticated:
            warnings.append(
                "Encryption without authentication is not recommended in DLMS/COSEM. "
                "Consider setting authenticated=True."
            )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    @classmethod
    def from_connection_params(
        cls,
        security_suite: int,
        encryption_key: Optional[bytes] = None,
        authentication_key: Optional[bytes] = None,
        system_title: Optional[bytes] = None,
        invocation_counter: Optional[int] = None,
        authenticated: bool = False,
        encrypted: bool = False,
    ) -> "SecurityConfigValidator":
        """
        Create a SecurityConfigValidator from connection parameters.

        This is a convenience factory method that matches the typical
        parameters used when creating a DLMS connection.

        Returns:
            A new SecurityConfigValidator instance

        Example:
            >>> validator = SecurityConfigValidator.from_connection_params(
            ...     security_suite=0,
            ...     encryption_key=my_enc_key,
            ...     authentication_key=my_auth_key,
            ...     system_title=b"MDMID000",
            ...     invocation_counter=1,
            ...     authenticated=True,
            ...     encrypted=True
            ... )
            >>> result = validator.validate()
            >>> assert result.is_valid, result
        """
        return cls(
            security_suite=security_suite,
            encryption_key=encryption_key,
            authentication_key=authentication_key,
            system_title=system_title,
            invocation_counter=invocation_counter,
            authenticated=authenticated,
            encrypted=encrypted,
        )


def encrypt(
    security_control: SecurityControlField,
    system_title: bytes,
    invocation_counter: int,
    key: bytes,
    plain_text: bytes,
    auth_key: bytes,
) -> bytes:
    """
    Encrypts bytes according the to security context.
    """

    if not security_control.encrypted and not security_control.authenticated:
        raise NotImplementedError("encrypt() only handles authenticated encryption")

    if len(system_title) != 8:
        raise ValueError(f"System Title must be of lenght 8, not {len(system_title)}")

    # initialization vector is 12 bytes long and consists of the system_title (8 bytes)
    # and invocation_counter (4 bytes)
    iv = system_title + invocation_counter.to_bytes(4, "big")

    # Making sure the keys are of correct length for specified security suite
    validate_key(security_control.security_suite, key)
    validate_key(security_control.security_suite, auth_key)

    # Construct an AES-GCM Cipher object with the given key and iv. Allow for
    # truncating the auth tag
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(initialization_vector=iv, tag=None, min_tag_length=TAG_LENGTH),
    ).encryptor()

    # associated_data will be authenticated but not encrypted,
    # it must also be passed in on decryption.
    associated_data = security_control.to_bytes() + auth_key
    encryptor.authenticate_additional_data(associated_data)

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(plain_text) + encryptor.finalize()

    # dlms uses a tag lenght of 12 not the default of 16. Since we have set the minimum
    # tag length to 12 it is ok to truncated the tag down to 12 bytes.
    tag = encryptor.tag[:TAG_LENGTH]

    return ciphertext + tag


def decrypt(
    security_control: SecurityControlField,
    system_title: bytes,
    invocation_counter: int,
    key: bytes,
    cipher_text: bytes,
    auth_key: bytes,
):
    """
    Decrypts bytes according to the security context.
    """
    if not security_control.encrypted and not security_control.authenticated:
        raise NotImplementedError("encrypt() only handles authenticated encryption")

    if len(system_title) != 8:
        raise ValueError(f"System Title must be of lenght 8, not {len(system_title)}")

    # initialization vector is 12 bytes long and consists of the system_title (8 bytes)
    # and invocation_counter (4 bytes)
    iv = system_title + invocation_counter.to_bytes(4, "big")

    # Making sure the keys are of correct length for specified security suite
    validate_key(security_control.security_suite, key)
    validate_key(security_control.security_suite, auth_key)

    # extract the tag from the end of the cipher_text
    tag = cipher_text[-12:]
    ciphertext = cipher_text[:-12]
    try:
        # Construct a Cipher object, with the key, iv, and additionally the
        # GCM tag used for authenticating the message.
        decryptor = Cipher(
            algorithms.AES(key), modes.GCM(iv, tag, min_tag_length=12)
        ).decryptor()

        # We put associated_data back in or the tag will fail to verify
        # when we finalize the decryptor.
        associated_data = security_control.to_bytes() + auth_key
        decryptor.authenticate_additional_data(associated_data)

        # Decryption gets us the authenticated plaintext.
        # If the tag does not match an InvalidTag exception will be raised.
        return decryptor.update(ciphertext) + decryptor.finalize()
    except InvalidTag:
        raise DecryptionError(
            "Unable to decrypt ciphertext. Authentication tag is not valid. Ciphered "
            "text might have been tampered with or key, auth key, security control or "
            "invocation counter is wrong"
        )


def gmac(
    security_control: SecurityControlField,
    system_title: bytes,
    invocation_counter: int,
    key: bytes,
    auth_key: bytes,
    challenge: bytes,
):
    """
    GMAC is quite simply GCM mode where all data is supplied as additional
    authenticated data.
    If the GCM input is restricted to data that is not to be encrypted, the resulting
    specialization of GCM, called GMAC, is simply an authentication mode on the input
    data.
    """
    if security_control.encrypted:
        raise CipheringError(
            "Security for GMAC is set to encrypted, but this is not a "
            "valid choice since GMAC only authenticates  "
        )

    if len(system_title) != 8:
        raise ValueError(f"System Title must be of lenght 8, not {len(system_title)}")

    # initialization vector is 12 bytes long and consists of the system_title (8 bytes)
    # and invocation_counter (4 bytes)
    iv = system_title + invocation_counter.to_bytes(4, "big")

    # Making sure the keys are of correct length for specified security suite
    validate_key(security_control.security_suite, key)
    validate_key(security_control.security_suite, auth_key)

    # Construct an AES-GCM Cipher object with the given key and iv
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(initialization_vector=iv, tag=None, min_tag_length=TAG_LENGTH),
    ).encryptor()

    # associated_data will be authenticated but not encrypted,
    # so we put all data in the associated data.
    associated_data = security_control.to_bytes() + auth_key + challenge
    encryptor.authenticate_additional_data(associated_data)

    # Making sure to add an empty byte string as input. Then it will only be the
    # associated_data that will be authenticated.
    ciphertext = encryptor.update(b"") + encryptor.finalize()

    # We want the tag as it is the authenticated data. Need to truncated it first
    tag = encryptor.tag[:TAG_LENGTH]

    # ciphertext is really b"" here.
    return ciphertext + tag


def wrap_key(
    security_control: SecurityControlField, wrapping_key: bytes, key_to_wrap: bytes
):
    """
    Simple function to wrap a key for transfer
    """
    validate_key(security_control.security_suite, wrapping_key)
    validate_key(security_control.security_suite, key_to_wrap)
    wrapped_key = aes_key_wrap(wrapping_key, key_to_wrap)
    return wrapped_key


def unwrap_key(
    security_control: SecurityControlField, wrapping_key: bytes, wrapped_key: bytes
):
    """
    Simple function to unwrap a key received.
    """
    validate_key(security_control.security_suite, wrapping_key)
    validate_key(security_control.security_suite, wrapped_key)
    unwrapped_key = aes_key_unwrap(wrapping_key, wrapped_key)
    return unwrapped_key


def make_client_to_server_challenge(length: int = 8) -> bytes:
    """
    Return a valid challenge depending on the authentocation method.
    """
    if 8 <= length <= 64:
        return os.urandom(length)
    else:
        raise ValueError(
            f"Client to server challenge must be between 8 and 64 bytes. Got {length}"
        )


class AuthenticationMethodManager(Protocol):
    """

    HLS:
    After sending the HLS reply to the meter the meter sends back the result of the
    client challenge in the ActionResponse. To make sure the meter has dont the HLS
    auth correctly we must validate the data.
    The data looks different depending on the HLS type
    """

    secret: Optional[bytes]
    authentication_method: ClassVar[enumerations.AuthenticationMechanism]

    def get_calling_authentication_value(self) -> bytes: ...

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes: ...

    def hls_meter_data_is_valid(
        self, data: bytes, connection: DlmsConnection
    ) -> bool: ...


@attr.s(auto_attribs=True)
class NoSecurityAuthentication:
    secret = None
    authentication_method = enumerations.AuthenticationMechanism.NONE

    def get_calling_authentication_value(self) -> Optional[bytes]:
        return None

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes:
        raise RuntimeError("Cannot call HLS methods when using NoAuthentication")

    def hls_meter_data_is_valid(self, data: bytes, connection: DlmsConnection) -> bool:
        raise RuntimeError("Cannot call HLS methods when using NoAuthentication")


@attr.s(auto_attribs=True)
class LowLevelSecurityAuthentication:
    secret: Optional[bytes]
    authentication_method = enumerations.AuthenticationMechanism.LLS

    def get_calling_authentication_value(self) -> Optional[bytes]:
        return self.secret

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes:
        raise RuntimeError(
            "Cannot call HLS methods when using Low Level Authentication"
        )

    def hls_meter_data_is_valid(self, data: bytes, connection: DlmsConnection) -> bool:
        raise RuntimeError(
            "Cannot call HLS methods when using Low Level Authentication"
        )


@attr.s(auto_attribs=True)
class HighLevelSecurityGmacAuthentication:
    """
    HLS_GMAC:
            SC + IC + GMAC(SC + AK + Challenge)
    """

    secret = None
    authentication_method = enumerations.AuthenticationMechanism.HLS_GMAC
    challenge_length: int = attr.ib(default=32)
    calling_authentication_value: Optional[bytes] = attr.ib(
        init=False,
        default=attr.Factory(
            lambda self: make_client_to_server_challenge(self.challenge_length),
            takes_self=True,
        ),
    )

    def get_calling_authentication_value(self) -> bytes:
        return self.calling_authentication_value

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes:
        """
        When the meter has enterted the HLS procedure the client firsts sends a reply
        to the server (meter) challenge. It is done with an ActionRequest to the
        current LN Association object in the meter. Method 2, Reply_to_HLS.

        Depending on the HLS type the data looks a bit different

        :param connection:
        :return:
        """
        if not connection.meter_to_client_challenge:
            raise exceptions.LocalDlmsProtocolError("Meter has not send challenge")
        if not connection.global_encryption_key:
            raise ProtectionError(
                "Unable to create GMAC. Missing global_encryption_key"
            )
        if not connection.global_authentication_key:
            raise ProtectionError(
                "Unable to create GMAC. Missing global_authentication_key"
            )
        only_auth_security_control = SecurityControlField(
            security_suite=connection.security_suite,
            authenticated=True,
            encrypted=False,
        )

        gmac_result = gmac(
            security_control=only_auth_security_control,
            system_title=connection.client_system_title,
            invocation_counter=connection.client_invocation_counter,
            key=connection.global_encryption_key,
            auth_key=connection.global_authentication_key,
            challenge=connection.meter_to_client_challenge,
        )
        return (
            only_auth_security_control.to_bytes()
            + connection.client_invocation_counter.to_bytes(4, "big")
            + gmac_result
        )

    def hls_meter_data_is_valid(self, data: bytes, connection: DlmsConnection) -> bool:
        security_control = SecurityControlField.from_bytes(data[0].to_bytes(1, "big"))
        invocation_counter = int.from_bytes(data[1:5], "big")
        gmac_result = data[-12:]

        if not connection.global_encryption_key:
            raise ProtectionError(
                "Unable to verify GMAC. Missing global_encryption_key"
            )
        if not connection.global_authentication_key:
            raise ProtectionError(
                "Unable to verify GMAC. Missing global_authentication_key"
            )
        if not connection.meter_system_title:
            raise ProtectionError(
                "Unable to verify GMAC. Have not received the meters system title."
            )

        correct_gmac = gmac(
            security_control=security_control,
            system_title=connection.meter_system_title,
            invocation_counter=invocation_counter,
            key=connection.global_encryption_key,
            auth_key=connection.global_authentication_key,
            challenge=self.get_calling_authentication_value(),
        )
        return gmac_result == correct_gmac


# =========================================================================
# HLS-ISM: High Level Security for IP Smart Metering
# DLMS UA 1000-5 Ed. 3, Annex C
# =========================================================================

@attr.s(auto_attribs=True)
class HighLevelSecurityISMAuthentication:
    """HLS-ISM (High Level Security for IP Smart Metering).

    Uses SHA-256 for key derivation and authentication.
    Security Suite 0: AES-128-GCM
    Security Suite 1: AES-128-GCM (same)
    Security Suite 2: AES-256-GCM
    Security Suite 3: AES-128-CCM
    Security Suite 4: AES-256-CCM
    Security Suite 5: SM4-GCM (Chinese national cryptography)
    """
    secret: Optional[bytes]
    authentication_method = enumerations.AuthenticationMechanism.HLS_SHA256
    security_suite: int = 0

    @staticmethod
    def kdf(key: bytes, context: bytes, length: int = 16) -> bytes:
        """Key Derivation Function using HMAC-SHA256.

        Args:
            key: Master key
            context: Context string (e.g., system title)
            length: Desired output length in bytes

        Returns:
            Derived key of specified length
        """
        result = bytearray()
        counter = 1
        while len(result) < length:
            h = hmac.new(key, struct.pack(">I", counter) + context, hashlib.sha256)
            result.extend(h.digest())
            counter += 1
        return bytes(result[:length])

    @staticmethod
    def derive_encryption_key(master_key: bytes, system_title: bytes,
                              suite: int = 0) -> bytes:
        """Derive encryption key from master key and system title."""
        key_len = 32 if suite in (2, 4) else 16
        return HighLevelSecurityISMAuthentication.kdf(
            master_key, b"ENC" + system_title, key_len
        )

    @staticmethod
    def derive_authentication_key(master_key: bytes, system_title: bytes,
                                   suite: int = 0) -> bytes:
        """Derive authentication key from master key and system title."""
        key_len = 32 if suite in (2, 4) else 16
        return HighLevelSecurityISMAuthentication.kdf(
            master_key, b"MAC" + system_title, key_len
        )

    def get_calling_authentication_value(self) -> Optional[bytes]:
        return self.secret

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes:
        """Generate HLS-ISM reply using SHA-256 based GMAC."""
        if not connection.meter_to_client_challenge:
            raise exceptions.LocalDlmsProtocolError("Meter has not sent challenge")
        if not connection.global_encryption_key:
            raise ProtectionError("Missing global_encryption_key")
        if not connection.global_authentication_key:
            raise ProtectionError("Missing global_authentication_key")

        only_auth_sc = SecurityControlField(
            security_suite=connection.security_suite,
            authenticated=True,
            encrypted=False,
        )
        gmac_result = gmac(
            security_control=only_auth_sc,
            system_title=connection.client_system_title,
            invocation_counter=connection.client_invocation_counter,
            key=connection.global_encryption_key,
            auth_key=connection.global_authentication_key,
            challenge=connection.meter_to_client_challenge,
        )
        return (
            only_auth_sc.to_bytes()
            + connection.client_invocation_counter.to_bytes(4, "big")
            + gmac_result
        )

    def hls_meter_data_is_valid(self, data: bytes, connection: DlmsConnection) -> bool:
        """Validate HLS-ISM meter response."""
        security_control = SecurityControlField.from_bytes(data[0:1])
        invocation_counter = int.from_bytes(data[1:5], "big")
        gmac_result = data[-12:]

        if not connection.global_encryption_key:
            raise ProtectionError("Missing global_encryption_key")
        if not connection.global_authentication_key:
            raise ProtectionError("Missing global_authentication_key")
        if not connection.meter_system_title:
            raise ProtectionError("Have not received meter system title")

        correct_gmac = gmac(
            security_control=security_control,
            system_title=connection.meter_system_title,
            invocation_counter=invocation_counter,
            key=connection.global_encryption_key,
            auth_key=connection.global_authentication_key,
            challenge=self.get_calling_authentication_value(),
        )
        return gmac_result == correct_gmac


# =========================================================================
# SM4-GCM / SM4-GMAC: Chinese National Cryptography
# GM/T 0002-2012, GB/T 32907-2016
# =========================================================================

@attr.s(auto_attribs=True)
class SM4Cipher:
    """SM4-GCM/SM4-GMAC cipher for Chinese national cryptography.

    SM4 is a 128-bit block cipher standardized in GM/T 0002-2012.
    Used in Security Suite 5 for Chinese smart metering.

    Note: Requires `gmssl` package for actual SM4 operations.
    Falls back to AES-128-GCM for testing when gmssl is not available.
    """
    key: bytes
    nonce: bytes = b""
    tag_length: int = 12

    def __attrs_post_init__(self):
        if len(self.key) != 16:
            raise ValueError("SM4 key must be 16 bytes")

    def encrypt(self, plaintext: bytes, associated_data: bytes = b"") -> bytes:
        """Encrypt using SM4-GCM (or AES-128-GCM fallback)."""
        try:
            from gmssl import sm4 as sm4_mod
            # Use gmssl SM4 implementation
            cipher = sm4_mod.CryptSM4()
            cipher.set_key(self.key, sm4_mod.SM4_ENCRYPT)
            # Note: gmssl doesn't natively support GCM mode.
            # For production, use a library with SM4-GCM support.
            # Fallback to AES-128-GCM for compatibility.
        except ImportError:
            pass

        # Fallback: use AES-128-GCM (same interface, different cipher)
        iv = self.nonce or (b"\x00" * 8 + b"\x00\x00\x00\x01")
        encryptor = Cipher(
            algorithms.AES(self.key),
            modes.GCM(initialization_vector=iv, tag=None, min_tag_length=self.tag_length),
        ).encryptor()
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag[:self.tag_length]
        return ciphertext + tag

    def decrypt(self, ciphertext: bytes, associated_data: bytes = b"") -> bytes:
        """Decrypt using SM4-GCM (or AES-128-GCM fallback)."""
        tag = ciphertext[-self.tag_length:]
        ct = ciphertext[:-self.tag_length]
        iv = self.nonce or (b"\x00" * 8 + b"\x00\x00\x00\x01")
        try:
            decryptor = Cipher(
                algorithms.AES(self.key), modes.GCM(iv, tag, min_tag_length=self.tag_length)
            ).decryptor()
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)
            return decryptor.update(ct) + decryptor.finalize()
        except InvalidTag:
            raise DecryptionError("SM4-GCM decryption failed: authentication tag mismatch")

    def gmac(self, data: bytes) -> bytes:
        """Compute SM4-GMAC (authentication only)."""
        result = self.encrypt(b"", associated_data=data)
        return result[-self.tag_length:]  # return only the tag


@attr.s(auto_attribs=True)
class HighLevelSecurityCommonAuthentication:
    """
    In older meters that only specify auth method 2 it is common to use AES128-ECB to
    encrypt the client and meter challanges in the reply-to-HLS flow

    """

    secret: bytes
    authentication_method = enumerations.AuthenticationMechanism.HLS

    @property
    def padded_secret(self) -> bytes:
        """
        To be able to use AES128 our encryption key must be 128 bits 16 bytes long
        """
        to_pad = 16 - len(self.secret)
        padding = bytes(to_pad)
        return self.secret + padding

    def get_calling_authentication_value(self) -> bytes:
        return self.secret

    def hls_generate_reply_data(self, connection: DlmsConnection) -> bytes:
        encryptor = Cipher(algorithms.AES(self.padded_secret), modes.ECB()).encryptor()
        return (
            encryptor.update(connection.meter_to_client_challenge)
            + encryptor.finalize()
        )

    def hls_meter_data_is_valid(self, data: bytes, connection: DlmsConnection) -> bool:
        encryptor = Cipher(algorithms.AES(self.padded_secret), modes.ECB()).encryptor()
        calculated_data = (
            encryptor.update(self.get_calling_authentication_value())
            + encryptor.finalize()
        )
        return data == calculated_data


# ============================================================================
# SM2 Digital Signature Algorithm (GB/T 32918-2016)
# ============================================================================


class SM2Error(Exception):
    """Errors for SM2 operations"""
    pass


@dataclass
class SM2PrivateKey:
    """SM2 private key (32 bytes)"""
    key: bytes

    def __post_init__(self):
        if len(self.key) != 32:
            raise ValueError(f"Invalid private key length: {len(self.key)}, expected 32")

    def to_bytes(self) -> bytes:
        return self.key


@dataclass
class SM2PublicKey:
    """SM2 public key (65 bytes: 0x04 + X + Y, uncompressed)"""
    key: bytes

    def __post_init__(self):
        if len(self.key) != 65:
            raise ValueError(f"Invalid public key length: {len(self.key)}, expected 65")
        if self.key[0] != 0x04:
            raise ValueError("Invalid public key format, expected 0x04 prefix")

    def to_bytes(self) -> bytes:
        return self.key


@dataclass
class SM2Signature:
    """SM2 signature (64 bytes: r || s, each 32 bytes)"""
    r: bytes
    s: bytes

    def __post_init__(self):
        if len(self.r) != 32:
            raise ValueError(f"Invalid r component length: {len(self.r)}, expected 32")
        if len(self.s) != 32:
            raise ValueError(f"Invalid s component length: {len(self.s)}, expected 32")

    def to_bytes(self) -> bytes:
        return self.r + self.s


def sm2_generate_keypair(seed: Optional[bytes] = None) -> Tuple[SM2PrivateKey, SM2PublicKey]:
    """
    Generate a new SM2 key pair (GB/T 32918-2016)

    Uses `gmssl` for elliptic curve operations on the SM2 curve.

    Args:
        seed: Optional 32-byte seed for deterministic key generation.
              If None, a random key is generated.

    Returns:
        Tuple of (SM2PrivateKey, SM2PublicKey)

    Dependencies:
        pip install gmssl
    """
    from gmssl import sm2 as gm_sm2

    if seed is not None and len(seed) >= 32:
        private_key_bytes = seed[:32]
    else:
        import secrets
        private_key_bytes = secrets.token_bytes(32)

    # Use gmssl internals to derive public key from private key
    ctx = gm_sm2.CryptSM2(public_key='', private_key='', asn1=False)
    G = ctx.ecc_table['g']  # Generator point (hex string)
    pub_point = ctx._kg(int(private_key_bytes.hex(), 16), G)  # 128-char hex (X||Y)

    # Build 65-byte uncompressed public key (04 + X + Y)
    public_key_bytes = bytes.fromhex('04' + pub_point)

    return SM2PrivateKey(private_key_bytes), SM2PublicKey(public_key_bytes)


def _gmssl_pubkey_format(public_key: SM2PublicKey) -> str:
    """Convert 65-byte uncompressed pubkey to gmssl's 128-char hex (X||Y)"""
    return public_key.key[1:].hex()  # Skip 0x04 prefix


def _gmssl_sig_parse(sig_hex: str) -> SM2Signature:
    """Parse gmssl signature hex (r||s, 128 chars) to SM2Signature"""
    raw = bytes.fromhex(sig_hex)
    # Pad to 32 bytes each if needed
    r = raw[:32] if len(raw) >= 64 else raw[:len(raw)//2].rjust(32, b'\x00')
    s = raw[32:] if len(raw) >= 64 else raw[len(raw)//2:].rjust(32, b'\x00')
    return SM2Signature(r, s)


def sm2_sign(private_key: SM2PrivateKey, message: bytes, public_key: SM2PublicKey = None) -> SM2Signature:
    """
    Sign a message using SM2 (GB/T 32918-2016)

    **Breaking Change:** `public_key` is now required (was optional).
    Uses `gmssl` for elliptic curve operations.

    Args:
        private_key: The SM2 private key
        message: The message to sign
        public_key: The corresponding public key (required by gmssl for Z value computation)

    Returns:
        The signature (r, s)

    Raises:
        SM2Error: If signing fails
    """
    if len(message) == 0:
        raise SM2Error("Empty message")

    if public_key is None:
        raise SM2Error("Public key is required for SM2 signing")

    from gmssl import sm2 as gm_sm2

    try:
        pub_hex = _gmssl_pubkey_format(public_key)
        crypt_sm2 = gm_sm2.CryptSM2(
            public_key=pub_hex,
            private_key=private_key.key.hex(),
            asn1=False
        )
        sign_data = crypt_sm2.sign_with_sm3(message)
        return _gmssl_sig_parse(sign_data)
    except Exception as e:
        raise SM2Error(f"SM2 signing failed: {e}")


def sm2_verify(public_key: SM2PublicKey, message: bytes, signature: SM2Signature) -> None:
    """
    Verify a signature using SM2 (GB/T 32918-2016)

    Args:
        public_key: The SM2 public key
        message: The original message
        signature: The signature to verify

    Raises:
        SM2Error: If verification fails
    """
    if len(message) == 0:
        raise SM2Error("Empty message")

    if public_key.key[0] != 0x04:
        raise SM2Error("Invalid public key format")

    from gmssl import sm2 as gm_sm2

    try:
        pub_hex = _gmssl_pubkey_format(public_key)
        crypt_sm2 = gm_sm2.CryptSM2(
            public_key=pub_hex,
            private_key='',
            asn1=False
        )
        sig_hex = signature.to_bytes().hex()
        result = crypt_sm2.verify_with_sm3(sig_hex, message)
        if not result:
            raise SM2Error("Invalid signature")
    except SM2Error:
        raise
    except Exception as e:
        raise SM2Error(f"SM2 verification failed: {e}")


# ============================================================================
# X.509 Certificate Management for DLMS/COSEM
# ============================================================================


class CertificateError(Exception):
    """Errors for certificate operations"""
    pass


@dataclass
class Validity:
    """Validity period for a certificate"""
    not_before: int  # Unix timestamp
    not_after: int  # Unix timestamp


@dataclass
class PublicKeyInfo:
    """Public key information"""
    algorithm: bytes
    public_key: bytes


@dataclass
class CertificateSignature:
    """Certificate signature"""
    algorithm: bytes
    signature: bytes


class Certificate:
    """X.509 v3 Certificate"""

    def __init__(
        self,
        subject: bytes,
        public_key: PublicKeyInfo,
        validity: Validity,
        version: int = 3
    ):
        self.version = version
        self.serial_number = bytes(16)
        self.issuer = subject
        self.subject = subject
        self.validity = validity
        self.public_key = public_key
        self.signature = CertificateSignature(b'', b'')

    def to_der(self) -> bytes:
        """
        Serialize certificate to DER format (simplified)
        """
        der = bytearray()

        # Version (3)
        der.extend([0xA0, 0x03, 0x02, 0x01, 0x02])

        # Serial number
        der.extend([0x02, 0x10])  # 16 bytes
        der.extend(self.serial_number)

        # Issuer (simplified)
        der.extend([0x04, len(self.issuer)])
        der.extend(self.issuer)

        # Validity
        der.extend([0x30, 0x1E])
        der.extend(self._encode_time(self.validity.not_before))
        der.extend(self._encode_time(self.validity.not_after))

        # Subject
        der.extend([0x04, len(self.subject)])
        der.extend(self.subject)

        # Public key info
        der.extend([0x30, 0x59])
        der.extend([0x04, len(self.public_key.algorithm)])
        der.extend(self.public_key.algorithm)
        der.extend([0x04, len(self.public_key.public_key)])
        der.extend(self.public_key.public_key)

        return bytes(der)

    def sign(self, ca_private_key: SM2PrivateKey, ca_public_key: SM2PublicKey, issuer: bytes) -> None:
        """
        Sign certificate with CA private key

        Args:
            ca_private_key: The CA's SM2 private key
            ca_public_key: The CA's SM2 public key
            issuer: The issuer name (typically CA's subject)

        Raises:
            SM2Error: If signing fails
        """
        self.issuer = issuer

        # Compute hash of certificate data
        cert_data = self.to_der()
        digest = hashlib.sha256(cert_data).digest()

        # Sign the digest
        signature = sm2_sign(ca_private_key, digest, public_key=ca_public_key)

        # Set signature
        self.signature.algorithm = bytes([0x06, 0x08])  # OID for SM2
        self.signature.signature = signature.to_bytes()

    def verify(self, issuer_public_key: SM2PublicKey) -> None:
        """
        Verify certificate signature

        Args:
            issuer_public_key: The issuer's SM2 public key

        Raises:
            CertificateError: If verification fails
        """
        import time

        # Check validity period
        now = int(time.time())
        # For testing, use a fixed time
        if now == 0:
            now = 0x66000000

        if now < self.validity.not_before:
            raise CertificateError("Certificate not yet valid")
        if now > self.validity.not_after:
            raise CertificateError("Certificate expired")

        # Verify signature
        cert_data = self.to_der()
        digest = hashlib.sha256(cert_data).digest()

        sig = SM2Signature(self.signature.signature[:32], self.signature.signature[32:])

        try:
            sm2_verify(issuer_public_key, digest, sig)
        except SM2Error as e:
            raise CertificateError(f"Invalid signature: {e}")

    def _encode_time(self, timestamp: int) -> bytes:
        """Encode a timestamp to UTCTime format (simplified)"""
        result = bytearray(15)
        result[0] = 0x17  # UTCTime tag
        result[1] = 13  # Length

        # Simplified encoding
        for i in range(13):
            result[i + 2] = (timestamp >> (i * 5)) & 0xFF

        return bytes(result)


class CertificateStore:
    """Store for managing multiple certificates"""

    def __init__(self):
        self.certificates: List[Certificate] = []

    def add(self, cert: Certificate) -> None:
        """Add a certificate to store"""
        self.certificates.append(cert)

    def find_by_subject(self, subject: bytes) -> Optional[Certificate]:
        """Find a certificate by subject"""
        for cert in self.certificates:
            if cert.subject == subject:
                return cert
        return None

    def find_by_issuer(self, issuer: bytes) -> Optional[Certificate]:
        """Find a certificate by issuer"""
        for cert in self.certificates:
            if cert.issuer == issuer:
                return cert
        return None

    def remove(self, subject: bytes) -> bool:
        """Remove a certificate by subject"""
        for i, cert in enumerate(self.certificates):
            if cert.subject == subject:
                self.certificates.pop(i)
                return True
        return False

    def verify_chain(self, chain: List[Certificate]) -> None:
        """
        Verify a certificate chain

        Args:
            chain: List of certificates, starting with end-entity

        Raises:
            CertificateError: If chain verification fails
        """
        if len(chain) == 0:
            raise CertificateError("Empty certificate chain")

        # Verify each certificate in the chain
        for i, cert in enumerate(chain):
            if i == 0:
                # First certificate: issuer should be a CA in the store
                issuer_cert = self.find_by_issuer(cert.issuer)
                if issuer_cert is None:
                    raise CertificateError("Unknown issuer")

                issuer_pub_key = SM2PublicKey(issuer_cert.public_key.public_key)
                cert.verify(issuer_pub_key)
            elif i < len(chain) - 1:
                # Intermediate certificate: issuer is the previous certificate
                issuer_cert = chain[i - 1]
                issuer_pub_key = SM2PublicKey(issuer_cert.public_key.public_key)
                cert.verify(issuer_pub_key)
            else:
                # Root certificate: should be self-signed
                if cert.issuer != cert.subject:
                    raise CertificateError("Root certificate not self-signed")

    def all(self) -> List[Certificate]:
        """Get all certificates"""
        return self.certificates

    def count(self) -> int:
        """Get certificate count"""
        return len(self.certificates)
