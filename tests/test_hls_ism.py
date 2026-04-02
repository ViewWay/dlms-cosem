"""Tests for HLS-ISM and SM4 security enhancements."""
import os
import pytest

from dlms_cosem.security import (
    SecurityControlField,
    SM4Cipher,
    HighLevelSecurityISMAuthentication,
)


class TestHLSISM:
    def test_kdf(self):
        key = os.urandom(16)
        context = b"test context"
        derived = HighLevelSecurityISMAuthentication.kdf(key, context, 16)
        assert len(derived) == 16
        # Same input should produce same output
        derived2 = HighLevelSecurityISMAuthentication.kdf(key, context, 16)
        assert derived == derived2

    def test_kdf_different_context(self):
        key = os.urandom(16)
        d1 = HighLevelSecurityISMAuthentication.kdf(key, b"ctx1", 16)
        d2 = HighLevelSecurityISMAuthentication.kdf(key, b"ctx2", 16)
        assert d1 != d2

    def test_derive_encryption_key(self):
        master = os.urandom(16)
        sys_title = os.urandom(8)
        enc_key = HighLevelSecurityISMAuthentication.derive_encryption_key(
            master, sys_title, suite=0
        )
        assert len(enc_key) == 16

    def test_derive_encryption_key_suite2(self):
        master = os.urandom(32)
        sys_title = os.urandom(8)
        enc_key = HighLevelSecurityISMAuthentication.derive_encryption_key(
            master, sys_title, suite=2
        )
        assert len(enc_key) == 32

    def test_derive_auth_key(self):
        master = os.urandom(16)
        sys_title = os.urandom(8)
        auth_key = HighLevelSecurityISMAuthentication.derive_authentication_key(
            master, sys_title
        )
        assert len(auth_key) == 16


class TestSM4Cipher:
    def test_create(self):
        cipher = SM4Cipher(key=os.urandom(16))
        assert cipher is not None

    def test_invalid_key_length(self):
        with pytest.raises(ValueError):
            SM4Cipher(key=os.urandom(15))

    def test_encrypt_decrypt(self):
        key = os.urandom(16)
        cipher = SM4Cipher(key=key)
        plaintext = b"hello world test data"
        ciphertext = cipher.encrypt(plaintext, associated_data=b"aad")
        # Should be plaintext + tag (12 bytes)
        decrypted = cipher.decrypt(ciphertext, associated_data=b"aad")
        assert decrypted == plaintext

    def test_decrypt_wrong_tag_fails(self):
        key = os.urandom(16)
        cipher = SM4Cipher(key=key)
        plaintext = b"test data"
        ciphertext = cipher.encrypt(plaintext)
        # Tamper with ciphertext
        tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
        with pytest.raises(Exception):
            cipher.decrypt(tampered)

    def test_gmac(self):
        key = os.urandom(16)
        cipher = SM4Cipher(key=key)
        data = b"authenticate this data"
        tag = cipher.gmac(data)
        assert len(tag) == 12


class TestSecurityControlField:
    def test_suite_3_allowed(self):
        scf = SecurityControlField(security_suite=3, authenticated=True)
        assert scf.security_suite == 3

    def test_suite_5_allowed(self):
        scf = SecurityControlField(security_suite=5, encrypted=True)
        assert scf.security_suite == 5

    def test_suite_6_rejected(self):
        with pytest.raises(ValueError):
            SecurityControlField(security_suite=6)

    def test_roundtrip(self):
        scf = SecurityControlField(
            security_suite=1, authenticated=True, encrypted=True
        )
        data = scf.to_bytes()
        parsed = SecurityControlField.from_bytes(data)
        assert parsed.security_suite == 1
        assert parsed.authenticated is True
        assert parsed.encrypted is True
