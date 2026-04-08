"""
Tests for X.509 certificate management
"""

import time
import pytest

from dlms_cosem.security import (
    sm2_generate_keypair,
    SM2PublicKey,
    Certificate,
    CertificateStore,
    Validity,
    PublicKeyInfo,
    CertificateError,
)


class TestCertificate:
    """Test Certificate class"""

    def test_new_certificate(self):
        """Test creating a new certificate"""
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"Test Subject",
            public_key=public_key_info,
            validity=validity,
        )

        assert cert.version == 3
        assert cert.subject == b"Test Subject"
        assert cert.issuer == b"Test Subject"

    def test_certificate_sign(self):
        """Test signing a certificate"""
        ca_priv, ca_pub = sm2_generate_keypair()
        _, end_pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=end_pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"End Entity",
            public_key=public_key_info,
            validity=validity,
        )

        cert.sign(ca_priv, ca_pub, b"CA Issuer")

        assert cert.issuer == b"CA Issuer"
        assert len(cert.signature.signature) == 64

    def test_certificate_to_der(self):
        """Test DER serialization"""
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"Test",
            public_key=public_key_info,
            validity=validity,
        )

        der = cert.to_der()
        assert len(der) > 0

    def test_certificate_verify_validity(self):
        """Test certificate validity check"""
        _, pub = sm2_generate_keypair()

        # Expired certificate
        expired_validity = Validity(
            not_before=0x66000000 - 31536000,
            not_after=0x66000000 - 86400,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"Expired",
            public_key=public_key_info,
            validity=expired_validity,
        )

        # Should fail due to expired certificate
        with pytest.raises(CertificateError, match="expired"):
            cert.verify(pub)


class TestCertificateStore:
    """Test CertificateStore class"""

    def test_store_add(self):
        """Test adding certificates to store"""
        store = CertificateStore()
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"Test",
            public_key=public_key_info,
            validity=validity,
        )

        store.add(cert)
        assert store.count() == 1

    def test_store_find(self):
        """Test finding certificates"""
        store = CertificateStore()
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"My Certificate",
            public_key=public_key_info,
            validity=validity,
        )

        store.add(cert)

        found = store.find_by_subject(b"My Certificate")
        assert found is not None
        assert found.subject == b"My Certificate"

    def test_store_remove(self):
        """Test removing certificates"""
        store = CertificateStore()
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert = Certificate(
            subject=b"Test",
            public_key=public_key_info,
            validity=validity,
        )

        store.add(cert)
        assert store.count() == 1

        store.remove(b"Test")
        assert store.count() == 0

    def test_certificate_chain(self):
        """Test certificate chain structure"""
        store = CertificateStore()

        # Create CA certificate
        seed1 = bytes([i + 1 for i in range(32)])
        ca_priv, ca_pub = sm2_generate_keypair(seed1)

        ca_validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 63072000,
        )

        ca_pub_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=ca_pub.to_bytes(),
        )

        ca_cert = Certificate(
            subject=b"Root CA",
            public_key=ca_pub_info,
            validity=ca_validity,
        )
        ca_cert.sign(ca_priv, ca_pub, b"Root CA")
        store.add(ca_cert)

        # Create intermediate certificate
        seed2 = bytes([i + 33 for i in range(32)])
        int_priv, int_pub = sm2_generate_keypair(seed2)

        int_validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        int_pub_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=int_pub.to_bytes(),
        )

        int_cert = Certificate(
            subject=b"Intermediate CA",
            public_key=int_pub_info,
            validity=int_validity,
        )
        int_cert.sign(ca_priv, ca_pub, b"Root CA")

        # Create end-entity certificate
        seed3 = bytes([i + 65 for i in range(32)])
        _, end_pub = sm2_generate_keypair(seed3)

        end_validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 15768000,
        )

        end_pub_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=end_pub.to_bytes(),
        )

        end_cert = Certificate(
            subject=b"End Entity",
            public_key=end_pub_info,
            validity=end_validity,
        )
        end_cert.sign(int_priv, int_pub, b"Intermediate CA")

        # Check chain structure
        chain = [end_cert, int_cert, ca_cert]
        assert len(chain) == 3
        assert chain[0].issuer == b"Intermediate CA"
        assert chain[1].issuer == b"Root CA"
        assert chain[2].issuer == b"Root CA"

    def test_store_all(self):
        """Test getting all certificates"""
        store = CertificateStore()
        _, pub = sm2_generate_keypair()

        validity = Validity(
            not_before=0x66000000,
            not_after=0x66000000 + 31536000,
        )

        public_key_info = PublicKeyInfo(
            algorithm=bytes([0x06, 0x08]),
            public_key=pub.to_bytes(),
        )

        cert1 = Certificate(
            subject=b"Test1",
            public_key=public_key_info,
            validity=validity,
        )
        cert2 = Certificate(
            subject=b"Test2",
            public_key=public_key_info,
            validity=validity,
        )

        store.add(cert1)
        store.add(cert2)

        all_certs = store.all()
        assert len(all_certs) == 2
