"""
Tests for KeyManager module.
"""
import os
import pytest
from pathlib import Path

from dlms_cosem.key_management import KeyManager, SecurityProfile
from dlms_cosem.key_management.key_storage import ConfigurationNotFoundError


class TestKeyManager:
    def test_generate_creates_new_profile(self):
        profile = KeyManager.generate(suite=0, name="test")
        assert isinstance(profile, SecurityProfile)
        assert profile.name == "test"
        assert profile.suite == 0
        assert len(profile.encryption_key) == 16

    def test_load_from_environment(self, monkeypatch):
        monkeypatch.setenv("DLMS_SECURITY_SUITE", "0")
        monkeypatch.setenv("DLMS_ENCRYPTION_KEY", "hex:00112233445566778899AABBCCDDEEFF")
        monkeypatch.setenv("DLMS_AUTHENTICATION_KEY", "hex:00112233445566778899AABBCCDDEEFF")

        profile = KeyManager.load()
        assert profile.suite == 0

    def test_load_from_toml_file(self, tmp_path):
        keys_file = tmp_path / "keys.toml"
        keys_file.write_text("""
[default]
suite = 0
encryption_key = "hex:00112233445566778899AABBCCDDEEFF"
authentication_key = "hex:00112233445566778899AABBCCDDEEFF"
""")

        profile = KeyManager.load(paths=[str(keys_file)])
        assert profile.suite == 0

    def test_save_creates_toml_file(self, tmp_path):
        profile = KeyManager.generate(suite=0)
        output_path = tmp_path / "output.toml"

        KeyManager.save(profile, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "suite = 0" in content

    def test_load_raises_when_not_found(self, tmp_path, monkeypatch):
        # Clear env vars and use empty tmp path
        for key in list(os.environ.keys()):
            if key.startswith("DLMS_"):
                monkeypatch.delenv(key, raising=False)

        with pytest.raises(ConfigurationNotFoundError):
            KeyManager.load(paths=[str(tmp_path)])

    def test_from_predefined_strategy(self):
        profile = KeyManager.from_strategy(
            "hls-gmac",
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
        )
        assert profile.name == "hls-gmac"
        assert profile.authenticated is True
