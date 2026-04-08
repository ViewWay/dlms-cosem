"""
Tests for KeyStorage backends.
"""
import os
import pytest
from pathlib import Path

from dlms_cosem.key_management import SecurityProfile
from dlms_cosem.key_management.key_storage import (
    EnvironmentStorage,
    FileStorage,
    ConfigurationNotFoundError,
)


class TestEnvironmentStorage:
    def test_load_from_environment_vars(self, monkeypatch):
        monkeypatch.setenv("DLMS_SECURITY_SUITE", "0")
        monkeypatch.setenv("DLMS_ENCRYPTION_KEY", "hex:00112233445566778899AABBCCDDEEFF")
        monkeypatch.setenv("DLMS_AUTHENTICATION_KEY", "hex:00112233445566778899AABBCCDDEEFF")

        storage = EnvironmentStorage()
        profile = storage.load()
        assert profile.suite == 0
        assert len(profile.encryption_key) == 16

    def test_load_returns_none_when_not_found(self, monkeypatch):
        # Clear all DLMS env vars
        for key in os.environ.copy():
            if key.startswith("DLMS_"):
                monkeypatch.delenv(key, raising=False)

        storage = EnvironmentStorage()
        with pytest.raises(ConfigurationNotFoundError):
            storage.load()


class TestFileStorage:
    def test_load_toml_file(self, tmp_path):
        toml_file = tmp_path / "keys.toml"
        toml_file.write_text("""
[default]
suite = 0
encryption_key = "hex:00112233445566778899AABBCCDDEEFF"
authentication_key = "hex:00112233445566778899AABBCCDDEEFF"
authenticated = true
encrypted = true
""")

        storage = FileStorage(str(toml_file))
        profile = storage.load("default")
        assert profile.name == "default"
        assert profile.suite == 0

    def test_save_toml_file(self, tmp_path):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
        )

        toml_file = tmp_path / "output.toml"
        storage = FileStorage(str(toml_file))
        storage.save(profile)

        content = toml_file.read_text()
        assert 'suite = 0' in content
        assert "hex:" in content
