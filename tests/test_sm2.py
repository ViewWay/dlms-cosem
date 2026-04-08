"""
Tests for SM2 digital signature implementation
"""

import pytest

from dlms_cosem.security import (
    sm2_generate_keypair,
    sm2_sign,
    sm2_verify,
    SM2PrivateKey,
    SM2PublicKey,
    SM2Signature,
    SM2Error,
)


class TestSM2GenerateKeyPair:
    """Test SM2 key pair generation"""

    def test_generate_keypair(self):
        """Test basic key pair generation"""
        priv, pub = sm2_generate_keypair()
        assert len(priv.key) == 32
        assert len(pub.key) == 65
        assert pub.key[0] == 0x04

    def test_generate_keypair_deterministic(self):
        """Test deterministic key pair generation"""
        seed = bytes([i + 1 for i in range(32)])
        priv1, pub1 = sm2_generate_keypair(seed)
        priv2, pub2 = sm2_generate_keypair(seed)

        assert priv1 == priv2
        assert pub1 == pub2


class TestSM2SignVerify:
    """Test SM2 signing and verification"""

    def test_sign_verify(self):
        """Test basic sign and verify"""
        priv, pub = sm2_generate_keypair()
        message = b"Hello, SM2!"

        signature = sm2_sign(priv, message, public_key=pub)
        sm2_verify(pub, message, signature)

    def test_verify_wrong_signature(self):
        """Test verification with wrong signature"""
        priv, pub = sm2_generate_keypair()
        message = b"Hello, SM2!"

        signature = sm2_sign(priv, message, public_key=pub)
        # Corrupt multiple bytes
        signature.r = bytes([b ^ 0xFF for b in signature.r])
        signature.s = bytes([b ^ 0xFF for b in signature.s])

        with pytest.raises(SM2Error):
            sm2_verify(pub, message, signature)

    def test_verify_wrong_message(self):
        """Test verification with wrong message"""
        priv, pub = sm2_generate_keypair()
        message = b"Hello, SM2!"

        signature = sm2_sign(priv, message, public_key=pub)
        wrong_message = b"Wrong message"

        with pytest.raises(SM2Error):
            sm2_verify(pub, wrong_message, signature)

    def test_sign_empty_message(self):
        """Test signing empty message"""
        priv, _ = sm2_generate_keypair()

        with pytest.raises(SM2Error, match="Empty message"):
            sm2_sign(priv, b"")

    def test_verify_empty_message(self):
        """Test verifying empty message"""
        _, pub = sm2_generate_keypair()
        signature = SM2Signature(bytes(32), bytes(32))

        with pytest.raises(SM2Error, match="Empty message"):
            sm2_verify(pub, b"", signature)

    def test_signature_size(self):
        """Test signature size"""
        priv, pub = sm2_generate_keypair()
        signature = sm2_sign(priv, b"test", public_key=pub)

        assert len(signature.r) == 32
        assert len(signature.s) == 32
        assert len(signature.to_bytes()) == 64

    def test_multiple_signatures_deterministic(self):
        """Test signatures with same seed produce same keys"""
        seed = bytes([i + 1 for i in range(32)])
        priv1, pub1 = sm2_generate_keypair(seed)
        priv2, pub2 = sm2_generate_keypair(seed)

        message = b"Test message"
        sig1 = sm2_sign(priv1, message, public_key=pub1)
        sig2 = sm2_sign(priv2, message, public_key=pub2)

        # Note: SM2 uses random k, so signatures differ each time
        # But both should verify
        sm2_verify(pub1, message, sig1)
        sm2_verify(pub2, message, sig2)


class TestSM2Conversions:
    """Test byte conversions"""

    def test_private_key_from_bytes(self):
        """Test private key from bytes"""
        priv, _ = sm2_generate_keypair()
        bytes_data = priv.to_bytes()

        priv2 = SM2PrivateKey(bytes_data)
        assert priv == priv2

    def test_public_key_from_bytes(self):
        """Test public key from bytes"""
        _, pub = sm2_generate_keypair()
        bytes_data = pub.to_bytes()

        pub2 = SM2PublicKey(bytes_data)
        assert pub == pub2

    def test_signature_from_bytes(self):
        """Test signature from bytes"""
        priv, pub = sm2_generate_keypair()
        signature = sm2_sign(priv, b"test", public_key=pub)
        bytes_data = signature.to_bytes()

        sig2 = SM2Signature(bytes_data[:32], bytes_data[32:])
        assert signature == sig2

    def test_private_key_invalid_length(self):
        """Test private key with invalid length"""
        with pytest.raises(ValueError, match="Invalid private key length"):
            SM2PrivateKey(b"short")

    def test_public_key_invalid_length(self):
        """Test public key with invalid length"""
        with pytest.raises(ValueError, match="Invalid public key length"):
            SM2PublicKey(b"short")

    def test_signature_invalid_length(self):
        """Test signature with invalid length"""
        with pytest.raises(ValueError, match="Invalid r component length"):
            SM2Signature(b"short", b"short")
