"""SM4 encryption benchmark using AES-128-GCM fallback (Python security module)."""

import timeit
import os
from dlms_cosem.security import encrypt, decrypt, SecurityControlField

# 16-byte SM4 key and 16-byte auth key
KEY = os.urandom(16)
AUTH_KEY = os.urandom(16)
SYSTEM_TITLE = b"\x01\x02\x03\x04\x05\x06\x07\x08"

# Security suite 5 (SM4-GCM) control field
SEC_CONTROL = SecurityControlField(
    security_suite=1,
    authenticated=True,
    encrypted=True,
)

# Typical DLMS APDU payload (GetResponse with register data)
PLAIN_TEXT = bytes([
    0xC1, 0x01, 0xC0, 0x01, 0x00, 0x06, 0x00, 0x00,
    0x01, 0x00, 0x00, 0xFF, 0x02, 0x12, 0x34, 0x56,
    0x78, 0x9A, 0xBC,
])


def bench_encrypt():
    """Benchmark SM4/AES-GCM encryption of DLMS APDU."""
    for _ in range(1000):
        encrypt(SEC_CONTROL, SYSTEM_TITLE, 1, KEY, PLAIN_TEXT, AUTH_KEY)


def bench_decrypt():
    """Benchmark SM4/AES-GCM decryption of DLMS APDU."""
    ciphertext = encrypt(SEC_CONTROL, SYSTEM_TITLE, 1, KEY, PLAIN_TEXT, AUTH_KEY)
    for _ in range(1000):
        decrypt(SEC_CONTROL, SYSTEM_TITLE, 1, KEY, ciphertext, AUTH_KEY)


if __name__ == "__main__":
    print("SM4 Encrypt:", timeit.timeit(bench_encrypt, number=100))
    print("SM4 Decrypt:", timeit.timeit(bench_decrypt, number=100))
