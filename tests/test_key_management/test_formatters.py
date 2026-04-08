"""
Tests for KeyFormatter module.
"""
import pytest
import base64

from dlms_cosem.key_management.formatters import KeyFormat, KeyFormatter


class TestKeyFormatter:
    def test_encode_hex(self):
        key = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        assert KeyFormatter.encode(key, KeyFormat.HEX) == "00112233445566778899aabbccddeeff"

    def test_encode_hex_uppercase(self):
        key = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        assert KeyFormatter.encode(key, KeyFormat.HEX, uppercase=True) == "00112233445566778899AABBCCDDEEFF"

    def test_encode_base64(self):
        key = b"test key!!"
        encoded = KeyFormatter.encode(key, KeyFormat.BASE64)
        assert encoded == base64.b64encode(key).decode()

    def test_decode_hex_with_prefix(self):
        data = "hex:00112233445566778899AABBCCDDEEFF"
        result = KeyFormatter.decode(data)
        assert result == bytes.fromhex("00112233445566778899AABBCCDDEEFF")

    def test_decode_base64_with_prefix(self):
        data = "base64:dGVzdCBrZXkhIQ=="
        result = KeyFormatter.decode(data)
        assert result == b"test key!!"

    def test_decode_hex_without_prefix(self):
        data = "00112233445566778899AABBCCDDEEFF"
        result = KeyFormatter.decode(data)
        assert result == bytes.fromhex("00112233445566778899AABBCCDDEEFF")

    def test_decode_raw_bytes(self):
        key = b"test key"
        assert KeyFormatter.decode(key) == key

    def test_auto_detect_hex_format(self):
        data = "00112233445566778899aabbccddeeff"
        result = KeyFormatter.decode(data)
        assert len(result) == 16

    def test_auto_detect_base64_format(self):
        data = base64.b64encode(b"test key!!").decode()
        result = KeyFormatter.decode(data)
        assert result == b"test key!!"

    def test_format_key_with_hex_prefix(self):
        key = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        assert KeyFormatter.format_key(key, "hex") == "hex:00112233445566778899aabbccddeeff"

    def test_format_key_with_base64_prefix(self):
        key = b"test key!!"
        assert KeyFormatter.format_key(key, "base64") == f"base64:{base64.b64encode(key).decode()}"
