"""
Key storage backends for DLMS/COSEM security configurations.

Supports loading/saving from environment variables, files (TOML/YAML/.env),
and optionally system keyring.
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from dlms_cosem.key_management.profiles import SecurityProfile
from dlms_cosem.key_management.formatters import KeyFormatter
from dlms_cosem.enumerations import AuthenticationMechanism


class ConfigurationNotFoundError(Exception):
    """Raised when a security configuration cannot be found."""


class KeyStorage(ABC):
    """Abstract base class for key storage backends."""

    @abstractmethod
    def load(self, profile_name: str = "default") -> SecurityProfile:
        """Load a security profile from storage."""
        pass

    def save(self, profile: SecurityProfile) -> None:
        """Save a security profile to storage (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support saving")


class EnvironmentStorage(KeyStorage):
    """Load security configuration from environment variables."""

    ENV_PREFIX = "DLMS_"

    def load(self, profile_name: str = "default") -> SecurityProfile:
        """
        Load from environment variables.

        Expected variables:
        - DLMS_SECURITY_SUITE (0, 1, 2)
        - DLMS_ENCRYPTION_KEY (hex:...)
        - DLMS_AUTHENTICATION_KEY (hex:...)
        - DLMS_SYSTEM_TITLE (optional)
        - DLMS_AUTHENTICATED (true/false, default true)
        - DLMS_ENCRYPTED (true/false, default true)
        """
        suite_str = os.getenv(f"{self.ENV_PREFIX}SECURITY_SUITE")
        if not suite_str:
            raise ConfigurationNotFoundError("DLMS_SECURITY_SUITE not set")

        enc_key_str = os.getenv(f"{self.ENV_PREFIX}ENCRYPTION_KEY")
        auth_key_str = os.getenv(f"{self.ENV_PREFIX}AUTHENTICATION_KEY")

        if not enc_key_str or not auth_key_str:
            raise ConfigurationNotFoundError(
                f"DLMS_ENCRYPTION_KEY and DLMS_AUTHENTICATION_KEY must be set"
            )

        suite = int(suite_str)
        encryption_key = KeyFormatter.decode(enc_key_str)
        authentication_key = KeyFormatter.decode(auth_key_str)

        return SecurityProfile(
            name=profile_name,
            suite=suite,
            encryption_key=encryption_key,
            authentication_key=authentication_key,
            system_title=bytes.fromhex(os.getenv(f"{self.ENV_PREFIX}SYSTEM_TITLE", ""))
            if os.getenv(f"{self.ENV_PREFIX}SYSTEM_TITLE")
            else b"",
            authenticated=os.getenv(f"{self.ENV_PREFIX}AUTHENTICATED", "true").lower() == "true",
            encrypted=os.getenv(f"{self.ENV_PREFIX}ENCRYPTED", "true").lower() == "true",
        )


class FileStorage(KeyStorage):
    """Load/save security configuration from files (TOML/YAML/.env)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, profile_name: str = "default") -> SecurityProfile:
        """Detect file type and load configuration."""
        if not self.path.exists():
            raise ConfigurationNotFoundError(f"File not found: {self.path}")

        suffix = self.path.suffix.lower()

        if suffix == ".toml":
            return self._load_toml(profile_name)
        elif suffix in (".yaml", ".yml"):
            return self._load_yaml(profile_name)
        elif suffix == ".env" or self.path.name == ".env":
            return self._load_dotenv()
        else:
            # Try to detect from content
            return self._load_auto_detect(profile_name)

    def _load_toml(self, profile_name: str) -> SecurityProfile:
        try:
            import tomli
        except ImportError:
            raise ImportError("tomli package required for TOML support. Install with: pip install tomli")

        with open(self.path, "rb") as f:
            data = tomli.load(f)

        if profile_name not in data:
            raise ConfigurationNotFoundError(f"Profile '{profile_name}' not found in {self.path}")

        profile_data = data[profile_name]
        return self._dict_to_profile(profile_name, profile_data)

    def _load_yaml(self, profile_name: str) -> SecurityProfile:
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML package required for YAML support. Install with: pip install pyyaml")

        with open(self.path) as f:
            data = yaml.safe_load(f)

        if profile_name not in data:
            raise ConfigurationNotFoundError(f"Profile '{profile_name}' not found in {self.path}")

        profile_data = data[profile_name]
        return self._dict_to_profile(profile_name, profile_data)

    def _load_dotenv(self) -> SecurityProfile:
        """Load from .env file format."""
        env_vars = {}
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        suite = int(env_vars.get("DLMS_SECURITY_SUITE", "0"))
        enc_key = KeyFormatter.decode(env_vars.get("DLMS_ENCRYPTION_KEY", ""))
        auth_key = KeyFormatter.decode(env_vars.get("DLMS_AUTHENTICATION_KEY", ""))

        return SecurityProfile(
            name="default",
            suite=suite,
            encryption_key=enc_key,
            authentication_key=auth_key,
            system_title=bytes.fromhex(env_vars.get("DLMS_SYSTEM_TITLE", ""))
            if env_vars.get("DLMS_SYSTEM_TITLE")
            else b"",
            authenticated=env_vars.get("DLMS_AUTHENTICATED", "true").lower() == "true",
            encrypted=env_vars.get("DLMS_ENCRYPTED", "true").lower() == "true",
        )

    def _load_auto_detect(self, profile_name: str) -> SecurityProfile:
        """Try to detect file format from content."""
        with open(self.path) as f:
            content = f.read()

        # Check for TOML-style sections
        if "[" in content:
            return self._load_toml(profile_name)
        # Check for YAML-style
        if ":" in content and not content.startswith("="):
            return self._load_yaml(profile_name)
        # Default to dotenv
        return self._load_dotenv()

    def _dict_to_profile(self, name: str, data: dict) -> SecurityProfile:
        """Convert dictionary to SecurityProfile."""
        enc_key_str = data.get("encryption_key", "")
        auth_key_str = data.get("authentication_key", "")

        return SecurityProfile(
            name=name,
            suite=int(data.get("suite", 0)),
            encryption_key=KeyFormatter.decode(enc_key_str),
            authentication_key=KeyFormatter.decode(auth_key_str),
            system_title=bytes.fromhex(data.get("system_title", ""))
            if data.get("system_title")
            else b"",
            authenticated=data.get("authenticated", True),
            encrypted=data.get("encrypted", True),
        )

    def save(self, profile: SecurityProfile) -> None:
        """Save profile to file (format based on extension)."""
        suffix = self.path.suffix.lower()

        if suffix == ".toml":
            self._save_toml(profile)
        elif suffix in (".yaml", ".yml"):
            self._save_yaml(profile)
        elif suffix == ".env" or self.path.name == ".env":
            self._save_dotenv(profile)
        else:
            # Default to TOML
            self._save_toml(profile)

    def _save_toml(self, profile: SecurityProfile) -> None:
        try:
            import tomli_w
        except ImportError:
            raise ImportError("tomli_w package required for TOML writing. Install with: pip install tomli-w")

        # Read existing if any
        try:
            import tomli
            with open(self.path, "rb") as f:
                data = tomli.load(f)
        except Exception:
            data = {}

        data[profile.name] = {
            "suite": profile.suite,
            "encryption_key": KeyFormatter.format_key(profile.encryption_key, "hex"),
            "authentication_key": KeyFormatter.format_key(profile.authentication_key, "hex"),
            "authenticated": profile.authenticated,
            "encrypted": profile.encrypted,
        }

        if profile.system_title:
            data[profile.name]["system_title"] = profile.system_title.hex()

        with open(self.path, "wb") as f:
            tomli_w.dump(data, f)

    def _save_yaml(self, profile: SecurityProfile) -> None:
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML package required. Install with: pip install pyyaml")

        # Read existing if any
        try:
            with open(self.path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}

        data[profile.name] = {
            "suite": profile.suite,
            "encryption_key": KeyFormatter.format_key(profile.encryption_key, "hex"),
            "authentication_key": KeyFormatter.format_key(profile.authentication_key, "hex"),
            "authenticated": profile.authenticated,
            "encrypted": profile.encrypted,
        }

        if profile.system_title:
            data[profile.name]["system_title"] = profile.system_title.hex()

        with open(self.path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def _save_dotenv(self, profile: SecurityProfile) -> None:
        with open(self.path, "w") as f:
            f.write(f"DLMS_SECURITY_SUITE={profile.suite}\n")
            f.write(f"DLMS_ENCRYPTION_KEY={KeyFormatter.format_key(profile.encryption_key, 'hex')}\n")
            f.write(f"DLMS_AUTHENTICATION_KEY={KeyFormatter.format_key(profile.authentication_key, 'hex')}\n")
            if profile.system_title:
                f.write(f"DLMS_SYSTEM_TITLE={profile.system_title.hex()}\n")
            f.write(f"DLMS_AUTHENTICATED={str(profile.authenticated).lower()}\n")
            f.write(f"DLMS_ENCRYPTED={str(profile.encrypted).lower()}\n")
