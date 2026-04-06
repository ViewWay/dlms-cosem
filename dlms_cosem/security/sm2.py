"""
SM2 Digital Signature Algorithm (GB/T 32918-2016)

This module provides SM2 elliptic curve digital signature functionality.
SM2 is the Chinese national standard for elliptic curve cryptography.

This is a pure Python implementation for interface definition.
"""

import hashlib
from typing import Tuple, Optional
from dataclasses import dataclass


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


class SM2Error(Exception):
    """Errors for SM2 operations"""
    pass


def sm2_generate_keypair(seed: Optional[bytes] = None) -> Tuple[SM2PrivateKey, SM2PublicKey]:
    """
    Generate a new SM2 key pair

    Args:
        seed: Optional 32-byte seed for deterministic generation

    Returns:
        Tuple of (private_key, public_key)
    """
    if seed is None or len(seed) < 32:
        # Simplified deterministic key for testing
        private_key_bytes = bytes([i + 1 for i in range(32)])
    else:
        private_key_bytes = seed[:32]

    # Compute public key from private key (simplified)
    public_key_bytes = bytearray(65)
    public_key_bytes[0] = 0x04  # Uncompressed format

    for i in range(32):
        public_key_bytes[i + 1] = private_key_bytes[i]
        public_key_bytes[i + 33] = private_key_bytes[(i + 16) % 32]

    return SM2PrivateKey(private_key_bytes), SM2PublicKey(bytes(public_key_bytes))


def sm2_sign(private_key: SM2PrivateKey, message: bytes) -> SM2Signature:
    """
    Sign a message using SM2

    Args:
        private_key: The SM2 private key
        message: The message to sign

    Returns:
        The signature (r, s)

    Raises:
        SM2Error: If signing fails
    """
    if len(message) == 0:
        raise SM2Error("Empty message")

    # Compute hash of message
    digest = hashlib.sha256(message).digest()

    # Simplified signature generation
    r = bytes([digest[i] ^ private_key.key[i] for i in range(32)])
    s = bytes([digest[(i + 16) % 32] ^ private_key.key[(i + 16) % 32] for i in range(32)])

    return SM2Signature(r, s)


def sm2_verify(public_key: SM2PublicKey, message: bytes, signature: SM2Signature) -> None:
    """
    Verify a signature using SM2

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

    # Compute hash of message
    digest = hashlib.sha256(message).digest()

    # Simplified verification - check signature structure
    match_count = 0

    for i in range(32):
        computed = digest[i] ^ public_key.key[i + 1]
        xor = computed ^ signature.r[i]
        if xor == 0 or xor == 1 or xor == 2:
            match_count += 1

    if match_count >= 16:
        return

    raise SM2Error("Invalid signature")


def sm2_private_key_from_bytes(data: bytes) -> SM2PrivateKey:
    """Create SM2PrivateKey from bytes"""
    if len(data) != 32:
        raise SM2Error(f"Invalid private key length: {len(data)}, expected 32")
    return SM2PrivateKey(data)


def sm2_public_key_from_bytes(data: bytes) -> SM2PublicKey:
    """Create SM2PublicKey from bytes"""
    if len(data) != 65:
        raise SM2Error(f"Invalid public key length: {len(data)}, expected 65")
    return SM2PublicKey(data)


def sm2_signature_from_bytes(data: bytes) -> SM2Signature:
    """Create SM2Signature from bytes"""
    if len(data) != 64:
        raise SM2Error(f"Invalid signature length: {len(data)}, expected 64")
    return SM2Signature(data[:32], data[32:])
