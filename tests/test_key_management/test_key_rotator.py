"""
Tests for KeyRotator module.
"""
import pytest

from dlms_cosem.key_management import KeyManager, KeyRotator, KeyRotationResult


class TestKeyRotator:
    def test_rotate_generates_new_keys(self):
        old_profile = KeyManager.generate(suite=0, name="test")
        old_enc_key = old_profile.encryption_key

        result = KeyRotator.rotate(old_profile)

        assert isinstance(result, KeyRotationResult)
        assert result.new_profile.encryption_key != old_enc_key
        assert result.new_profile.name == "test"

    def test_rotate_keeps_suite_if_not_specified(self):
        old_profile = KeyManager.generate(suite=2, name="test")

        result = KeyRotator.rotate(old_profile)

        assert result.new_profile.suite == 2

    def test_rotate_can_change_suite(self):
        old_profile = KeyManager.generate(suite=0, name="test")

        result = KeyRotator.rotate(old_profile, new_suite=2)

        assert result.new_profile.suite == 2
        assert len(result.new_profile.encryption_key) == 32

    def test_rotate_saves_legacy_keys_when_requested(self):
        old_profile = KeyManager.generate(suite=0, name="test")

        result = KeyRotator.rotate(old_profile, keep_old_keys=True)

        assert result.legacy_key is not None
        assert "encryption_key" in result.legacy_key

    def test_rotate_result_contains_old_profile(self):
        old_profile = KeyManager.generate(suite=0, name="test")

        result = KeyRotator.rotate(old_profile)

        assert result.old_profile is old_profile

    def test_rotation_id_is_timestamp(self):
        profile = KeyManager.generate(suite=0, name="test")

        result = KeyRotator.rotate(profile)

        # Should be in format YYYYMMDD_HHMMSS
        assert "_" in result.rotation_id
        assert len(result.rotation_id) == 15
