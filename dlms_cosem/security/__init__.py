"""
DLMS/COSEM Security Package

This package contains security-related modules for DLMS/COSEM, including:
- SM2 digital signature algorithm
- X.509 certificate management
"""

from dlms_cosem.security.sm2 import (
    SM2PrivateKey,
    SM2PublicKey,
    SM2Signature,
    SM2Error,
    sm2_generate_keypair,
    sm2_sign,
    sm2_verify,
    sm2_private_key_from_bytes,
    sm2_public_key_from_bytes,
    sm2_signature_from_bytes,
)

from dlms_cosem.security.certificate import (
    Certificate,
    CertificateStore,
    CertificateError,
    Validity,
    PublicKeyInfo,
    CertificateSignature,
)

__all__ = [
    # SM2
    "SM2PrivateKey",
    "SM2PublicKey",
    "SM2Signature",
    "SM2Error",
    "sm2_generate_keypair",
    "sm2_sign",
    "sm2_verify",
    "sm2_private_key_from_bytes",
    "sm2_public_key_from_bytes",
    "sm2_signature_from_bytes",
    # Certificate
    "Certificate",
    "CertificateStore",
    "CertificateError",
    "Validity",
    "PublicKeyInfo",
    "CertificateSignature",
]
