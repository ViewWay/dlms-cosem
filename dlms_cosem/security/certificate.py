"""
X.509 Certificate Management for DLMS/COSEM

This module provides X.509 certificate structures and management
as specified in Green Book Edition 9, Section 9.2.6.4.
"""

import hashlib
import time
from typing import List, Optional
from dataclasses import dataclass

from dlms_cosem.security.sm2 import SM2PrivateKey, SM2PublicKey, SM2Signature, sm2_sign, sm2_verify, SM2Error


@dataclass
class Validity:
    """Validity period for a certificate"""
    not_before: int  # Unix timestamp
    not_after: int   # Unix timestamp


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

    def sign(self, ca_private_key: SM2PrivateKey, issuer: bytes) -> None:
        """
        Sign certificate with CA private key

        Args:
            ca_private_key: The CA's SM2 private key
            issuer: The issuer name (typically CA's subject)

        Raises:
            SM2Error: If signing fails
        """
        self.issuer = issuer

        # Compute hash of certificate data
        cert_data = self.to_der()
        digest = hashlib.sha256(cert_data).digest()

        # Sign the digest
        signature = sm2_sign(ca_private_key, digest)

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
        # Check validity period
        now = int(time.time())

        # For testing, use a fixed time
        if now == 0:
            now = 0x66000000  # Approximate 2026-04-06

        if now < self.validity.not_before:
            raise CertificateError("Certificate not yet valid")
        if now > self.validity.not_after:
            raise CertificateError("Certificate expired")

        # Verify signature
        cert_data = self.to_der()
        digest = hashlib.sha256(cert_data).digest()

        from dlms_cosem.security.sm2 import sm2_signature_from_bytes
        signature = sm2_signature_from_bytes(self.signature.signature)

        try:
            sm2_verify(issuer_public_key, digest, signature)
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
        """Add a certificate to the store"""
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

                from dlms_cosem.security.sm2 import sm2_public_key_from_bytes
                issuer_pub_key = sm2_public_key_from_bytes(issuer_cert.public_key.public_key)
                cert.verify(issuer_pub_key)
            elif i < len(chain) - 1:
                # Intermediate certificate: issuer is the previous certificate
                issuer_cert = chain[i - 1]
                from dlms_cosem.security.sm2 import sm2_public_key_from_bytes
                issuer_pub_key = sm2_public_key_from_bytes(issuer_cert.public_key.public_key)
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


class CertificateError(Exception):
    """Errors for certificate operations"""
    pass
