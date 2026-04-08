"""
Tests for KeyGenerator module.
"""
import pytest

from dlms_cosem.key_management.key_generator import KeyGenerator, KeyPair
from dlms_cosem.exceptions import InvalidSecuritySuiteError


class TestKeyGenerator:
    def test_generate_key_suite_0_returns_16_bytes(self):
        key = KeyGenerator.generate_key(0)
        assert len(key) == 16

    def test_generate_key_suite_1_returns_16_bytes(self):
        key = KeyGenerator.generate_key(1)
        assert len(key) == 16

    def test_generate_key_suite_2_returns_32_bytes(self):
        key = KeyGenerator.generate_key(2)
        assert len(key) == 32

    def test_generate_key_invalid_suite_raises(self):
        with pytest.raises(InvalidSecuritySuiteError):
            KeyGenerator.generate_key(99)

    def test_generate_key_pair_returns_same_keys(self):
        pair = KeyGenerator.generate_key_pair(0)
        assert isinstance(pair, KeyPair)
        assert len(pair.encryption_key) == 16
        assert len(pair.authentication_key) == 16

    def test_generate_key_pair_can_have_different_keys(self):
        pair = KeyGenerator.generate_key_pair(0, same_key=False)
        assert pair.encryption_key != pair.authentication_key

    def test_generate_system_title_format(self):
        title = KeyGenerator.generate_system_title("MDM")
        assert len(title) == 8
        assert title[:3] == b"MDM"

    def test_generate_system_title_default_manufacturer(self):
        title = KeyGenerator.generate_system_title()
        assert len(title) == 8
        assert len(title[:3]) == 3

    def test_generated_keys_are_unique(self):
        keys = [KeyGenerator.generate_key(0) for _ in range(100)]
        assert len(set(keys)) == 100
