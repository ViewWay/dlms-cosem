from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.ciphers.base import Cipher
import pytest

from dlms_cosem.security import (
    SecurityConfigValidator,
    SecuritySuite,
    SecuritySuiteNumber,
    SecurityControlField,
    ValidationResult,
    decrypt,
    encrypt,
    gmac,
    validate_challenge,
    validate_invocation_counter,
    validate_key,
    validate_key_length,
    validate_security_suite,
    validate_system_title,
)
from dlms_cosem.exceptions import (
    InvalidSecurityConfigurationError,
    InvalidSecuritySuiteError,
    KeyLengthError,
    SecuritySuiteError,
)


def test_encrypt():
    key = b"SUCHINSECUREKIND"
    auth_key = key

    text = b"SUPER_SECRET_TEXT"

    ctext = encrypt(
        key=key,
        auth_key=auth_key,
        invocation_counter=1,
        security_control=SecurityControlField(
            security_suite=0, authenticated=True, encrypted=True
        ),
        system_title=b"12345678",
        plain_text=text,
    )

    print(ctext)

    out = decrypt(
        key=key,
        auth_key=auth_key,
        invocation_counter=1,
        security_control=SecurityControlField(
            security_suite=0, authenticated=True, encrypted=True
        ),
        system_title=b"12345678",
        cipher_text=ctext,
    )

    assert text == out


def test_encrypt_authenticated():
    security_control = SecurityControlField(
        security_suite=0, authenticated=True, encrypted=True
    )
    encryption_key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    authentication_key = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    system_title = bytes.fromhex("4D4D4D0000BC614E")
    invocation_counter = int.from_bytes(bytes.fromhex("01234567"), "big")
    # Get request attr 2 of clock object.
    plain_data = bytes.fromhex("C0010000080000010000FF0200")

    ciphered_text = bytes.fromhex("411312FF935A47566827C467BC7D825C3BE4A77C3FCC056B6B")

    assert (
        encrypt(
            security_control=security_control,
            key=encryption_key,
            auth_key=authentication_key,
            system_title=system_title,
            invocation_counter=invocation_counter,
            plain_text=plain_data,
        )
        == ciphered_text
    )


def test_decrypt_authenticated():
    security_control = SecurityControlField(
        security_suite=0, authenticated=True, encrypted=True
    )
    encryption_key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    authentication_key = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    system_title = bytes.fromhex("4D4D4D0000BC614E")
    invocation_counter = int.from_bytes(bytes.fromhex("01234567"), "big")
    # Get request attr 2 of clock object.
    plain_data = bytes.fromhex("C0010000080000010000FF0200")

    ciphered_text = bytes.fromhex("411312FF935A47566827C467BC7D825C3BE4A77C3FCC056B6B")

    assert (
        decrypt(
            security_control=security_control,
            key=encryption_key,
            auth_key=authentication_key,
            system_title=system_title,
            invocation_counter=invocation_counter,
            cipher_text=ciphered_text,
        )
        == plain_data
    )


def test_gmac():
    encryption_key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    authentication_key = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    security_control = SecurityControlField(
        security_suite=0, authenticated=True, encrypted=False
    )
    client_invocation_counter = int.from_bytes(bytes.fromhex("00000001"), "big")
    client_system_title = bytes.fromhex("4D4D4D0000000001")
    # server_system_title = bytes.fromhex("4D4D4D0000BC614E")
    # server_invocation_counter = int.from_bytes(bytes.fromhex("01234567"), "big")
    # client_to_server_challenge = bytes.fromhex("4B35366956616759")
    server_to_client_challenge = bytes.fromhex("503677524A323146")
    result = gmac(
        security_control=security_control,
        key=encryption_key,
        auth_key=authentication_key,
        invocation_counter=client_invocation_counter,
        system_title=client_system_title,
        challenge=server_to_client_challenge,
    )
    assert len(result) == 12
    assert result == bytes.fromhex("1A52FE7DD3E72748973C1E28")


def test_gmac2():
    encryption_key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    authentication_key = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    security_control = SecurityControlField(
        security_suite=0, authenticated=True, encrypted=False
    )
    client_invocation_counter = int.from_bytes(bytes.fromhex("00000001"), "big")
    client_system_title = bytes.fromhex("4D4D4D0000000001")
    # server_system_title = bytes.fromhex("4D4D4D0000BC614E")
    # server_invocation_counter = int.from_bytes(bytes.fromhex("01234567"), "big")
    # client_to_server_challenge = bytes.fromhex("4B35366956616759")
    server_to_client_challenge = bytes.fromhex("503677524A323146")

    iv = client_system_title + client_invocation_counter.to_bytes(4, "big")

    assert iv == bytes.fromhex("4D4D4D000000000100000001")

    # Construct an AES-GCM Cipher object with the given key and iv
    encryptor = Cipher(
        algorithms.AES(encryption_key),
        modes.GCM(initialization_vector=iv, tag=None, min_tag_length=12),
    ).encryptor()

    # associated_data will be authenticated but not encrypted,
    # it must also be passed in on decryption.
    associated_data = (
        security_control.to_bytes() + authentication_key + server_to_client_challenge
    )

    assert associated_data == bytes.fromhex(
        "10D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF503677524A323146"
    )
    encryptor.authenticate_additional_data(associated_data)

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(b"") + encryptor.finalize()

    # dlms uses a tag lenght of 12 not the default of 16. Since we have set the minimum
    # tag length to 12 it is ok to truncated the tag.
    tag = encryptor.tag[:12]

    assert ciphertext == b""
    result = ciphertext + tag

    assert result == bytes.fromhex("1A52FE7DD3E72748973C1E28")


# =============================================================================
# Security Suite Tests
# =============================================================================


class TestSecuritySuite:
    """Tests for SecuritySuite class."""

    def test_from_number_suite_0(self):
        suite = SecuritySuite.from_number(0)
        assert suite.number == 0
        assert suite.key_length == 16
        assert suite.algorithm == "AES-128-GCM"
        assert suite.key_bits == 128

    def test_from_number_suite_1(self):
        suite = SecuritySuite.from_number(1)
        assert suite.number == 1
        assert suite.key_length == 16
        assert suite.algorithm == "AES-128-GCM"
        assert suite.key_bits == 128

    def test_from_number_suite_2(self):
        suite = SecuritySuite.from_number(2)
        assert suite.number == 2
        assert suite.key_length == 32
        assert suite.algorithm == "AES-256-GCM"
        assert suite.key_bits == 256

    def test_from_number_invalid_suite(self):
        with pytest.raises(InvalidSecuritySuiteError) as exc_info:
            SecuritySuite.from_number(3)
        assert "Invalid security suite number: 3" in str(exc_info.value)
        assert "Valid security suites are: 0, 1, 2" in str(exc_info.value)

    def test_validate_key_success(self):
        suite = SecuritySuite.from_number(0)
        # Should not raise
        suite.validate_key(b"0123456789ABCDEF")

    def test_validate_key_wrong_length(self):
        suite = SecuritySuite.from_number(0)
        with pytest.raises(KeyLengthError) as exc_info:
            suite.validate_key(b"short")
        assert "key length is 5 bytes" in str(exc_info.value)
        assert "requires 16 bytes (128 bits)" in str(exc_info.value)

    def test_validate_key_suite_2_success(self):
        suite = SecuritySuite.from_number(2)
        # 32 bytes for AES-256
        suite.validate_key(b"0123456789ABCDEFGHIJ0123456789AB")

    def test_validate_key_suite_2_wrong_length(self):
        suite = SecuritySuite.from_number(2)
        with pytest.raises(KeyLengthError) as exc_info:
            suite.validate_key(b"0123456789ABCDEF")
        assert "key length is 16 bytes" in str(exc_info.value)
        assert "requires 32 bytes (256 bits)" in str(exc_info.value)

    def test_str_representation(self):
        suite = SecuritySuite.from_number(0)
        assert str(suite) == "Security Suite 0 (AES-128-GCM, 128-bit)"


# =============================================================================
# Validation Function Tests
# =============================================================================


class TestValidateSecuritySuite:
    """Tests for validate_security_suite function."""

    def test_validate_security_suite_0(self):
        suite = validate_security_suite(0)
        assert suite.number == 0

    def test_validate_security_suite_1(self):
        suite = validate_security_suite(1)
        assert suite.number == 1

    def test_validate_security_suite_2(self):
        suite = validate_security_suite(2)
        assert suite.number == 2

    def test_validate_security_suite_invalid(self):
        with pytest.raises(InvalidSecuritySuiteError):
            validate_security_suite(99)


class TestValidateKey:
    """Tests for validate_key function."""

    def test_validate_key_suite_0_success(self):
        validate_key(0, b"0123456789ABCDEF")

    def test_validate_key_suite_1_success(self):
        validate_key(1, b"0123456789ABCDEF")

    def test_validate_key_suite_2_success(self):
        validate_key(2, b"0123456789ABCDEFGHIJ0123456789AB")

    def test_validate_key_suite_0_wrong_length(self):
        with pytest.raises(KeyLengthError):
            validate_key(0, b"short")

    def test_validate_key_suite_2_wrong_length(self):
        with pytest.raises(KeyLengthError):
            validate_key(2, b"0123456789ABCDEF")


class TestValidateKeyLength:
    """Tests for validate_key_length function."""

    def test_validate_key_length_with_custom_name(self):
        validate_key_length(0, b"0123456789ABCDEF", "my_custom_key")

    def test_validate_key_length_wrong_length_custom_name(self):
        with pytest.raises(KeyLengthError) as exc_info:
            validate_key_length(0, b"short", "my_encryption_key")
        assert "my_encryption_key" in str(exc_info.value)


class TestValidateSystemTitle:
    """Tests for validate_system_title function."""

    def test_validate_system_title_success(self):
        validate_system_title(b"12345678")

    def test_validate_system_title_too_short(self):
        with pytest.raises(ValueError) as exc_info:
            validate_system_title(b"1234")
        assert "System title must be exactly 8 bytes" in str(exc_info.value)
        assert "Got 4 bytes" in str(exc_info.value)

    def test_validate_system_title_too_long(self):
        with pytest.raises(ValueError) as exc_info:
            validate_system_title(b"1234567890")
        assert "System title must be exactly 8 bytes" in str(exc_info.value)
        assert "Got 10 bytes" in str(exc_info.value)

    def test_validate_system_title_error_message(self):
        with pytest.raises(ValueError) as exc_info:
            validate_system_title(b"short")
        assert "3-byte manufacturer ID" in str(exc_info.value)
        assert "5-byte unique identifier" in str(exc_info.value)


class TestValidateInvocationCounter:
    """Tests for validate_invocation_counter function."""

    def test_validate_invocation_counter_success(self):
        validate_invocation_counter(0)
        validate_invocation_counter(1)
        validate_invocation_counter(0xFFFFFFFF)

    def test_validate_invocation_counter_negative(self):
        with pytest.raises(ValueError) as exc_info:
            validate_invocation_counter(-1)
        assert "Invocation counter must be a 32-bit unsigned integer" in str(exc_info.value)

    def test_validate_invocation_counter_too_large(self):
        with pytest.raises(ValueError) as exc_info:
            validate_invocation_counter(0x100000000)
        assert "Invocation counter must be a 32-bit unsigned integer" in str(exc_info.value)

    def test_validate_invocation_counter_wrong_type(self):
        with pytest.raises(ValueError) as exc_info:
            validate_invocation_counter("not an int")
        assert "must be an integer" in str(exc_info.value)


class TestValidateChallenge:
    """Tests for validate_challenge function."""

    def test_validate_challenge_minimum(self):
        validate_challenge(b"12345678")

    def test_validate_challenge_maximum(self):
        validate_challenge(b"1" * 64)

    def test_validate_challenge_too_short(self):
        with pytest.raises(ValueError) as exc_info:
            validate_challenge(b"1234")
        assert "must be between 8 and 64 bytes" in str(exc_info.value)

    def test_validate_challenge_too_long(self):
        with pytest.raises(ValueError) as exc_info:
            validate_challenge(b"1" * 65)
        assert "must be between 8 and 64 bytes" in str(exc_info.value)

    def test_validate_challenge_custom_name(self):
        with pytest.raises(ValueError) as exc_info:
            validate_challenge(b"short", "client_challenge")
        assert "client_challenge" in str(exc_info.value)


# =============================================================================
# SecurityConfigValidator Tests
# =============================================================================


class TestSecurityConfigValidator:
    """Tests for SecurityConfigValidator class."""

    def test_valid_configuration_suite_0(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            system_title=b"MDMID000",
            invocation_counter=1,
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_configuration_suite_2(self):
        validator = SecurityConfigValidator(
            security_suite=2,
            encryption_key=b"0123456789ABCDEFGHIJ0123456789AB",
            authentication_key=b"0123456789ABCDEFGHIJ0123456789AB",
            system_title=b"MDMID000",
            invocation_counter=1,
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_suite_number(self):
        validator = SecurityConfigValidator(
            security_suite=99,
            encryption_key=b"0123456789ABCDEF",
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("Invalid security suite number: 99" in e for e in result.errors)

    def test_wrong_key_length_suite_0(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            encryption_key=b"short",
            authentication_key=b"short",
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("encryption_key length" in e for e in result.errors)

    def test_wrong_key_length_suite_2(self):
        validator = SecurityConfigValidator(
            security_suite=2,
            encryption_key=b"0123456789ABCDEF",  # 16 bytes, but Suite 2 needs 32
            authentication_key=b"0123456789ABCDEF",
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("32 bytes (256 bits)" in e for e in result.errors)

    def test_missing_keys_when_authenticated(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("Encryption key is required" in e for e in result.errors)
        assert any("Authentication key is required" in e for e in result.errors)

    def test_invalid_system_title(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            system_title=b"short",  # Wrong length
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("System title" in e for e in result.errors)

    def test_invalid_invocation_counter(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            invocation_counter=-1,
        )
        result = validator.validate()
        assert not result.is_valid
        assert any("Invocation counter" in e for e in result.errors)

    def test_encryption_without_authentication_warning(self):
        validator = SecurityConfigValidator(
            security_suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            encrypted=True,
            authenticated=False,
        )
        result = validator.validate()
        assert result.is_valid  # Still valid, just a warning
        assert any("Encryption without authentication" in w for w in result.warnings)

    def test_from_connection_params(self):
        validator = SecurityConfigValidator.from_connection_params(
            security_suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            system_title=b"MDMID000",
            invocation_counter=1,
            authenticated=True,
            encrypted=True,
        )
        result = validator.validate()
        assert result.is_valid

    def test_validation_result_str_valid(self):
        result = ValidationResult(True, [], ["warning 1"])
        assert "✓ Security configuration is valid" in str(result)
        assert "warning 1" in str(result)

    def test_validation_result_str_invalid(self):
        result = ValidationResult(False, ["error 1", "error 2"], [])
        assert "✗ Security configuration is invalid" in str(result)
        assert "error 1" in str(result)
        assert "error 2" in str(result)
