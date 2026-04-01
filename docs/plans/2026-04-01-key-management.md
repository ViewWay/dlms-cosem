# Key Management Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive key management system for DLMS/COSEM that supports key generation, storage (env vars/files/keyring), rotation, and format conversion.

**Architecture:** Modular design with `KeyManager` as the unified entry point, pluggable storage backends (Environment/File/Keyring), and support for multiple configuration formats (TOML/YAML/.env).

**Tech Stack:** Python 3.9+, dataclasses, protocols, cryptography (existing), tomli/toml-w, pyyaml (optional)

---

## Task 1: Create Security Package Structure

**Files:**
- Create: `dlms_cosem/security/__init__.py`
- Modify: `dlms_cosem/security.py` (keep existing, move new code to new package)

**Step 1: Create the security package**

```python
# dlms_cosem/security/__init__.py
"""
Security and key management utilities for DLMS/COSEM.

This package provides:
- Key generation for Security Suites 0/1/2
- Key storage backends (environment, files, keyring)
- Security profile management
- Key rotation utilities
"""

from dlms_cosem.security.key_generator import KeyGenerator, KeyPair
from dlms_cosem.security.formatters import KeyFormat, KeyFormatter
from dlms_cosem.security.profiles import SecurityProfile, SECURITY_STRATEGIES
from dlms_cosem.security.key_manager import KeyManager
from dlms_cosem.security.key_rotator import KeyRotator, KeyRotationResult

__all__ = [
    "KeyGenerator",
    "KeyPair",
    "KeyFormat",
    "KeyFormatter",
    "SecurityProfile",
    "SECURITY_STRATEGIES",
    "KeyManager",
    "KeyRotator",
    "KeyRotationResult",
]
```

**Step 2: Run tests**

Run: `python -c "from dlms_cosem.security import KeyManager; print('OK')"`
Expected: ImportError (modules not created yet)

**Step 3: Commit**

```bash
git add dlms_cosem/security/__init__.py
git commit -m "feat: create security package structure"
```

---

## Task 2: Create KeyGenerator Module

**Files:**
- Create: `dlms_cosem/security/key_generator.py`
- Create: `tests/test_security/test_key_generator.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_key_generator.py
import pytest

from dlms_cosem.security import KeyGenerator, KeyPair
from dlms_cosem.security.key_generator import INSUFFICIENT_ENTROPY


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_security/test_key_generator.py -v`
Expected: ImportError (module doesn't exist)

**Step 3: Write minimal implementation**

```python
# dlms_cosem/security/key_generator.py
import os
from dataclasses import dataclass
from typing import Literal

from dlms_cosem.security.security_suite import SecuritySuite
from dlms_cosem.exceptions import InvalidSecuritySuiteError


@dataclass(frozen=True)
class KeyPair:
    """A pair of encryption and authentication keys."""

    encryption_key: bytes
    authentication_key: bytes


class KeyGenerator:
    """
    Generate cryptographic keys according to DLMS/COSEM Security Suite specifications.

    Security Suite 0/1: 16-byte keys (AES-128)
    Security Suite 2: 32-byte keys (AES-256)
    """

    @staticmethod
    def generate_key(suite: int) -> bytes:
        """
        Generate a random encryption key for the specified security suite.

        Args:
            suite: Security suite number (0, 1, or 2)

        Returns:
            Random key bytes of appropriate length

        Raises:
            InvalidSecuritySuiteError: If suite is not valid
        """
        security_suite = SecuritySuite.from_number(suite)
        return os.urandom(security_suite.key_length)

    @staticmethod
    def generate_key_pair(
        suite: int, same_key: bool = True
    ) -> KeyPair:
        """
        Generate an encryption key and authentication key.

        In DLMS/COSEM, the encryption and authentication keys can be the same
        or different depending on the deployment.

        Args:
            suite: Security suite number (0, 1, or 2)
            same_key: If True, use the same key for both (default)

        Returns:
            KeyPair with encryption and authentication keys
        """
        key = KeyGenerator.generate_key(suite)
        if same_key:
            return KeyPair(encryption_key=key, authentication_key=key)

        return KeyPair(
            encryption_key=KeyGenerator.generate_key(suite),
            authentication_key=KeyGenerator.generate_key(suite),
        )

    @staticmethod
    def generate_system_title(manufacturer_id: str = "MDM") -> bytes:
        """
        Generate a DLMS/COSEM system title.

        The system title is 8 bytes:
        - 3 bytes: Manufacturer ID (FLAG ID)
        - 5 bytes: Unique identifier

        Args:
            manufacturer_id: 3-character manufacturer ID

        Returns:
            8-byte system title
        """
        if len(manufacturer_id) < 3:
            manufacturer_id = manufacturer_id.ljust(3, "X")
        unique = os.urandom(5)
        return manufacturer_id[:3].encode("ascii").upper() + unique
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_security/test_key_generator.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/key_generator.py tests/test_security/test_key_generator.py
git commit -m "feat: implement KeyGenerator for DLMS/COSEM keys"
```

---

## Task 3: Create KeyFormatter Module

**Files:**
- Create: `dlms_cosem/security/formatters.py`
- Create: `tests/test_security/test_formatters.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_formatters.py
import pytest
import base64

from dlms_cosem.security import KeyFormat, KeyFormatter


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

    def test_encode_raw_returns_bytes(self):
        key = b"test key"
        assert KeyFormatter.encode(key, KeyFormat.RAW) == key

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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_security/test_formatters.py -v`
Expected: ImportError

**Step 3: Write minimal implementation**

```python
# dlms_cosem/security/formatters.py
import base64
from enum import Enum

from typing import Literal


class KeyFormat(str, Enum):
    """Key format types for encoding and decoding."""

    RAW = "raw"
    HEX = "hex"
    BASE64 = "base64"
    PEM = "pem"


class KeyFormatter:
    """
    Format conversion for cryptographic keys.

    Supports multiple formats with automatic detection:
    - hex:00112233... or 00112233...
    - base64:ABC123... or ABC123...
    - Raw bytes
    """

    @staticmethod
    def encode(
        key: bytes, format: KeyFormat | Literal["raw", "hex", "base64"], uppercase: bool = False
    ) -> str:
        """
        Encode a key to the specified format.

        Args:
            key: Key bytes to encode
            format: Target format
            uppercase: For hex, use uppercase letters

        Returns:
            Encoded key string
        """
        format = KeyFormat(format)

        if format == KeyFormat.HEX:
            result = key.hex()
            return result.upper() if uppercase else result
        elif format == KeyFormat.BASE64:
            return base64.b64encode(key).decode()
        elif format == KeyFormat.RAW:
            return key.decode("latin1") if isinstance(key, bytes) else key
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def decode(data: str | bytes) -> bytes:
        """
        Decode a key from string or bytes.

        Automatically detects format from prefix:
        - "hex:..." for hexadecimal
        - "base64:..." for Base64
        - Otherwise attempts auto-detection

        Args:
            data: Key data to decode

        Returns:
            Decoded key bytes
        """
        if isinstance(data, bytes):
            return data

        data = data.strip()

        # Check for explicit prefix
        if data.startswith("hex:"):
            return bytes.fromhex(data[4:])
        elif data.startswith("base64:"):
            return base64.b64decode(data[4:])

        # Auto-detect
        # Try hex first (even length, valid hex chars)
        if len(data) % 2 == 0:
            try:
                return bytes.fromhex(data)
            except ValueError:
                pass

        # Try base64
        try:
            return base64.b64decode(data)
        except Exception:
            pass

        raise ValueError(
            f"Cannot decode key data: {data[:20]}... "
            f"Use 'hex:...' or 'base64:...' prefix to specify format"
        )

    @staticmethod
    def format_key(
        key: bytes, format: Literal["hex", "base64"] = "hex", prefix: bool = True
    ) -> str:
        """
        Format a key with optional prefix.

        Args:
            key: Key bytes to format
            format: Target format ("hex" or "base64")
            prefix: Whether to add format prefix

        Returns:
            Formatted key string
        """
        encoded = KeyFormatter.encode(key, KeyFormat(format))
        if prefix:
            return f"{format}:{encoded}"
        return encoded
```

**Step 4: Run tests**

Run: `pytest tests/test_security/test_formatters.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/formatters.py tests/test_security/test_formatters.py
git commit -m "feat: implement KeyFormatter for format conversion"
```

---

## Task 4: Create SecurityProfile Module

**Files:**
- Create: `dlms_cosem/security/profiles.py`
- Create: `tests/test_security/test_profiles.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_profiles.py
import pytest

from dlms_cosem.security import SecurityProfile, SECURITY_STRATEGIES
from dlms_cosem.enumerations import AuthenticationMechanism


class TestSecurityProfile:
    def test_create_minimal_profile(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
        )
        assert profile.name == "test"
        assert profile.suite == 0

    def test_profile_with_hls_gmac(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            authentication_method=AuthenticationMechanism.HLS_GMAC,
            authenticated=True,
            encrypted=True,
        )
        assert profile.authenticated is True
        assert profile.encrypted is True

    def test_validate_profile_checks_key_length(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"short",  # Wrong length
            authentication_key=b"0123456789ABCDEF",
        )
        with pytest.raises(KeyLengthError):
            profile.validate()

    def test_to_dict_conversion(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            system_title=b"MDMID000",
        )
        data = profile.to_dict()
        assert data["name"] == "test"
        assert data["suite"] == 0
        assert "encryption_key" in data


class TestSecurityStrategies:
    def test_none_strategy(self):
        profile = SECURITY_STRATEGIES["none"]
        assert profile.suite == 0
        assert profile.authenticated is False
        assert profile.encrypted is False

    def test_lls_strategy(self):
        profile = SECURITY_STRATEGIES["lls"]
        assert profile.authentication_method == AuthenticationMechanism.LLS

    def test_hls_gmac_strategy(self):
        profile = SECURITY_STRATEGIES["hls-gmac"]
        assert profile.authentication_method == AuthenticationMechanism.HLS_GMAC
        assert profile.authenticated is True
        assert profile.encrypted is True

    def test_hls_suite2_strategy(self):
        profile = SECURITY_STRATEGIES["hls-suite2"]
        assert profile.suite == 2

    def test_all_strategies_are_valid(self):
        for name, profile in SECURITY_STRATEGIES.items():
            profile.validate()  # Should not raise
```

**Step 2: Run tests**

Run: `pytest tests/test_security/test_profiles.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
# dlms_cosem/security/profiles.py
from dataclasses import dataclass, field
from typing import Required

from dlms_cosem.enumerations import AuthenticationMechanism
from dlms_cosem.exceptions import KeyLengthError, InvalidSecuritySuiteError
from dlms_cosem.security.formatters import KeyFormatter
from dlms_cosem.security.security_suite import SecuritySuite


@dataclass
class SecurityProfile:
    """
    A complete DLMS/COSEM security configuration.

    Attributes:
        name: Profile identifier (e.g., "default", "meter1")
        suite: Security suite number (0, 1, or 2)
        encryption_key: Encryption key bytes
        authentication_key: Authentication key bytes
        system_title: 8-byte system title
        authentication_method: Authentication mechanism to use
        authenticated: Whether to use authentication
        encrypted: Whether to use encryption
    """

    name: str
    suite: int
    encryption_key: bytes
    authentication_key: bytes
    system_title: bytes = b""
    authentication_method: AuthenticationMechanism = AuthenticationMechanism.HLS_GMAC
    authenticated: bool = True
    encrypted: bool = True

    def validate(self) -> None:
        """
        Validate the security profile.

        Raises:
            InvalidSecuritySuiteError: If suite number is invalid
            KeyLengthError: If key lengths don't match suite requirements
        """
        suite_info = SecuritySuite.from_number(self.suite)
        suite_info.validate_key(self.encryption_key, "encryption_key")
        suite_info.validate_key(self.authentication_key, "authentication_key")

    def to_dict(self, include_secrets: bool = False) -> dict:
        """
        Convert profile to dictionary.

        Args:
            include_secrets: Whether to include actual key values

        Returns:
            Dictionary representation
        """
        data = {
            "name": self.name,
            "suite": self.suite,
            "system_title": self.system_title.hex() if self.system_title else "",
            "authentication_method": self.authentication_method.name,
            "authenticated": self.authenticated,
            "encrypted": self.encrypted,
        }

        if include_secrets:
            data["encryption_key"] = KeyFormatter.format_key(self.encryption_key, "hex")
            data["authentication_key"] = KeyFormatter.format_key(
                self.authentication_key, "hex"
            )
        else:
            data["encryption_key"] = "***"
            data["authentication_key"] = "***"

        return data


# Predefined security strategies for common use cases
SECURITY_STRATEGIES: dict[str, SecurityProfile] = {
    "none": SecurityProfile(
        name="none",
        suite=0,
        encryption_key=b"",
        authentication_key=b"",
        authentication_method=AuthenticationMechanism.NONE,
        authenticated=False,
        encrypted=False,
    ),
    "lls": SecurityProfile(
        name="lls",
        suite=0,
        encryption_key=b"",
        authentication_key=b"",  # Will be set by user
        authentication_method=AuthenticationMechanism.LLS,
        authenticated=True,
        encrypted=False,
    ),
    "hls-gmac": SecurityProfile(
        name="hls-gmac",
        suite=0,
        encryption_key=b"",  # Will be set by user
        authentication_key=b"",  # Will be set by user
        authentication_method=AuthenticationMechanism.HLS_GMAC,
        authenticated=True,
        encrypted=True,
    ),
    "hls-suite2": SecurityProfile(
        name="hls-suite2",
        suite=2,
        encryption_key=b"",  # Will be set by user (32 bytes)
        authentication_key=b"",  # Will be set by user (32 bytes)
        authentication_method=AuthenticationMechanism.HLS_GMAC,
        authenticated=True,
        encrypted=True,
    ),
}
```

**Step 4: Run tests**

Run: `pytest tests/test_security/test_profiles.py -v`
Expected: Fix any import issues, all tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/profiles.py tests/test_security/test_profiles.py
git commit -m "feat: implement SecurityProfile and predefined strategies"
```

---

## Task 5: Create SecuritySuite Reference Module

**Files:**
- Create: `dlms_cosem/security/security_suite.py`
- Modify: Move SecuritySuite from security.py to new module
- Update: `dlms_cosem/security/__init__.py` imports

**Step 1: Create security_suite.py**

```python
# dlms_cosem/security/security_suite.py
"""
Moved from dlms_cosem/security.py to organize the security package.
"""
from dataclasses import dataclass
from enum import IntEnum
from dlms_cosem.exceptions import InvalidSecuritySuiteError, KeyLengthError


class SecuritySuiteNumber(IntEnum):
    """
    DLMS/COSEM Security Suite numbers as defined in the DLMS UA Yellow Book.
    """

    SUITE_0 = 0
    """AES-128-GCM with 16-byte keys (128 bits)"""

    SUITE_1 = 1
    """AES-128-GCM with 16-byte keys (128 bits) - Same as Suite 0"""

    SUITE_2 = 2
    """AES-256-GCM with 32-byte keys (256 bits)"""


@dataclass(frozen=True)
class SecuritySuite:
    """
    Represents a DLMS/COSEM Security Suite with its configuration requirements.
    """

    number: int
    key_length: int
    algorithm: str
    key_bits: int

    @classmethod
    def from_number(cls, suite_number: int) -> "SecuritySuite":
        """Get a SecuritySuite instance from its number."""
        try:
            return _SECURITY_SUITES[suite_number]
        except KeyError:
            valid_suites = ", ".join(str(n) for n in _SECURITY_SUITES.keys())
            raise InvalidSecuritySuiteError(
                f"Invalid security suite number: {suite_number}. "
                f"Valid security suites are: {valid_suites}"
            )

    def validate_key(self, key: bytes, key_name: str = "key") -> None:
        """Validate that a key has the correct length for this security suite."""
        if len(key) != self.key_length:
            raise KeyLengthError(
                f"{key_name} length is {len(key)} bytes, but "
                f"Security Suite {self.number} ({self.algorithm}) requires "
                f"{self.key_length} bytes ({self.key_bits} bits). "
                f"Got: {key.hex()[:32]}{'...' if len(key) > 16 else ''}"
            )

    def __str__(self) -> str:
        return f"Security Suite {self.number} ({self.algorithm}, {self.key_bits}-bit)"


_SECURITY_SUITES: dict[int, SecuritySuite] = {
    0: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_0,
        key_length=16,
        algorithm="AES-128-GCM",
        key_bits=128,
    ),
    1: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_1,
        key_length=16,
        algorithm="AES-128-GCM",
        key_bits=128,
    ),
    2: SecuritySuite(
        number=SecuritySuiteNumber.SUITE_2,
        key_length=32,
        algorithm="AES-256-GCM",
        key_bits=256,
    ),
}
```

**Step 2: Update security.py to import from new module**

```python
# Add to dlms_cosem/security.py top imports
from dlms_cosem.security.security_suite import SecuritySuite, SecuritySuiteNumber
```

**Step 3: Update __init__.py**

```python
# Add to dlms_cosem/security/__init__.py
from dlms_cosem.security.security_suite import SecuritySuite, SecuritySuiteNumber
```

**Step 4: Run tests**

Run: `pytest tests/test_security.py -v`
Expected: All existing tests still pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/security_suite.py dlms_cosem/security/__init__.py dlms_cosem/security.py
git commit -m "refactor: extract SecuritySuite to dedicated module"
```

---

## Task 6: Create KeyStorage Backends

**Files:**
- Create: `dlms_cosem/security/key_storage.py`
- Create: `tests/test_security/test_key_storage.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_key_storage.py
import os
import pytest
from pathlib import Path

from dlms_cosem.security import SecurityProfile
from dlms_cosem.security.key_storage import (
    KeyStorage,
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

    def test_load_yaml_file(self, tmp_path):
        yaml_file = tmp_path / "keys.yaml"
        yaml_file.write_text("""
default:
  suite: 0
  encryption_key: hex:00112233445566778899AABBCCDDEEFF
  authentication_key: hex:00112233445566778899AABBCCDDEEFF
  authenticated: true
  encrypted: true
""")

        storage = FileStorage(str(yaml_file))
        profile = storage.load("default")
        assert profile.name == "default"

    def test_load_dotenv_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("""
DLMS_SECURITY_SUITE=0
DLMS_ENCRYPTION_KEY=hex:00112233445566778899AABBCCDDEEFF
DLMS_AUTHENTICATION_KEY=hex:00112233445566778899AABBCCDDEEFF
DLMS_AUTHENTICATED=true
DLMS_ENCRYPTED=true
""")

        storage = FileStorage(str(env_file))
        profile = storage.load()
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
```

**Step 2: Run tests**

Run: `pytest tests/test_security/test_key_storage.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
# dlms_cosem/security/key_storage.py
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from dlms_cosem.security.profiles import SecurityProfile
from dlms_cosem.security.formatters import KeyFormatter
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

        with open(self.path, "w") as f:
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
```

**Step 4: Run tests**

Run: `pytest tests/test_security/test_key_storage.py -v`
Expected: Fix any issues, tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/key_storage.py tests/test_security/test_key_storage.py
git commit -m "feat: implement key storage backends (env, file formats)"
```

---

## Task 7: Create KeyManager Main Class

**Files:**
- Create: `dlms_cosem/security/key_manager.py`
- Create: `tests/test_security/test_key_manager.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_key_manager.py
import os
import pytest
from pathlib import Path

from dlms_cosem.security import KeyManager, SecurityProfile
from dlms_cosem.security.key_storage import ConfigurationNotFoundError


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

    def test_load_fallback_to_file_when_env_not_set(self, tmp_path, monkeypatch):
        # Clear env vars
        for key in list(os.environ.keys()):
            if key.startswith("DLMS_"):
                monkeypatch.delenv(key, raising=False)

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

    def test_load_from_predefined_strategy(self):
        profile = KeyManager.from_strategy("hls-gmac")
        assert profile.name == "hls-gmac"
        assert profile.authenticated is True
        assert profile.encrypted is True

    def test_load_from_strategy_with_custom_keys(self):
        profile = KeyManager.from_strategy(
            "hls-gmac",
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
        )
        assert len(profile.encryption_key) == 16
```

**Step 2: Run tests**

Run: `pytest tests/test_security/test_key_manager.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
# dlms_cosem/security/key_manager.py
import os
from pathlib import Path
from typing import Optional

from dlms_cosem.security.key_generator import KeyGenerator
from dlms_cosem.security.key_storage import (
    KeyStorage,
    EnvironmentStorage,
    FileStorage,
    ConfigurationNotFoundError,
)
from dlms_cosem.security.profiles import SecurityProfile, SECURITY_STRATEGIES
from dlms_cosem.security.formatters import KeyFormatter


class KeyManager:
    """
    Unified entry point for DLMS/COSEM key management.

    Provides methods for generating, loading, and saving security configurations.
    Automatically searches multiple sources in priority order.
    """

    DEFAULT_LOOKUP_PATHS = [
        ".env",
        "keys.toml",
        "keys.yaml",
        "keys.yml",
        "~/.dlms/keys.toml",
        "/etc/dlms/keys.toml",
    ]

    @staticmethod
    def generate(
        suite: int,
        name: str = "generated",
        same_key: bool = True,
        system_title: Optional[bytes] = None,
    ) -> SecurityProfile:
        """
        Generate a new security profile with random keys.

        Args:
            suite: Security suite number (0, 1, or 2)
            name: Profile name
            same_key: Use same key for encryption and authentication
            system_title: Optional system title (auto-generated if not provided)

        Returns:
            New SecurityProfile with generated keys
        """
        key_pair = KeyGenerator.generate_key_pair(suite, same_key)

        if system_title is None:
            system_title = KeyGenerator.generate_system_title()

        return SecurityProfile(
            name=name,
            suite=suite,
            encryption_key=key_pair.encryption_key,
            authentication_key=key_pair.authentication_key,
            system_title=system_title,
        )

    @classmethod
    def load(
        cls,
        profile_name: str = "default",
        paths: Optional[list[str]] = None,
    ) -> SecurityProfile:
        """
        Load a security profile from available sources.

        Search priority:
        1. Environment variables (DLMS_*)
        2. Configuration files in provided paths (or defaults)
        3. User directory (~/.dlms/)
        4. System directory (/etc/dlms/)

        Args:
            profile_name: Profile name to load from files
            paths: Custom list of paths to search

        Returns:
            Loaded SecurityProfile

        Raises:
            ConfigurationNotFoundError: If no configuration found
        """
        # 1. Try environment variables first
        try:
            return EnvironmentStorage().load(profile_name)
        except ConfigurationNotFoundError:
            pass

        # 2-4. Try configuration files
        lookup_paths = paths or cls.DEFAULT_LOOKUP_PATHS
        for path_str in lookup_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                try:
                    return FileStorage(path).load(profile_name)
                except (ConfigurationNotFoundError, Exception):
                    continue

        raise ConfigurationNotFoundError(
            f"Security profile '{profile_name}' not found. "
            f"Searched: {lookup_paths}. "
            f"Set environment variables (DLMS_SECURITY_SUITE, etc.) or create a configuration file."
        )

    @staticmethod
    def save(
        profile: SecurityProfile,
        path: str,
        format: Optional[str] = None,
    ) -> None:
        """
        Save a security profile to a file.

        Args:
            profile: SecurityProfile to save
            path: Output file path
            format: Format override ("toml", "yaml", "env")
        """
        storage = FileStorage(path)
        storage.save(profile)

    @staticmethod
    def from_strategy(
        strategy_name: str,
        **overrides,
    ) -> SecurityProfile:
        """
        Create a SecurityProfile from a predefined strategy.

        Args:
            strategy_name: Strategy name ("none", "lls", "hls-gmac", "hls-suite2")
            **overrides: Fields to override (encryption_key, etc.)

        Returns:
            SecurityProfile based on the strategy

        Example:
            profile = KeyManager.from_strategy(
                "hls-gmac",
                encryption_key=my_key,
                authentication_key=my_key,
            )
        """
        if strategy_name not in SECURITY_STRATEGIES:
            available = ", ".join(SECURITY_STRATEGIES.keys())
            raise ValueError(
                f"Unknown strategy: {strategy_name}. Available: {available}"
            )

        # Get base strategy
        base = SECURITY_STRATEGIES[strategy_name]

        # Apply overrides (create new instance with replaced fields)
        from dataclasses import replace

        return replace(base, **overrides)

    @staticmethod
    def validate(profile: SecurityProfile) -> None:
        """
        Validate a security profile.

        Args:
            profile: SecurityProfile to validate

        Raises:
            KeyLengthError: If key lengths are incorrect
            InvalidSecuritySuiteError: If suite is invalid
        """
        profile.validate()
```

**Step 4: Run tests**

Run: `pytest tests/test_security/test_key_manager.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/key_manager.py tests/test_security/test_key_manager.py
git commit -m "feat: implement KeyManager unified entry point"
```

---

## Task 8: Create KeyRotator Module

**Files:**
- Create: `dlms_cosem/security/key_rotator.py`
- Create: `tests/test_security/test_key_rotator.py`

**Step 1: Write the failing tests**

```python
# tests/test_security/test_key_rotator.py
import pytest
from datetime import datetime

from dlms_cosem.security import KeyManager, KeyRotator, KeyRotationResult, SecurityProfile


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
        assert len(result.rotation_id) == 17
```

**Step 2: Run tests**

Run: `pytest tests/test_security/test_key_rotator.py -v`
Expected: ImportError

**Step 3: Write implementation**

```python
# dlms_cosem/security/key_rotator.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dlms_cosem.security.key_generator import KeyGenerator
from dlms_cosem.security.profiles import SecurityProfile
from dlms_cosem.security.formatters import KeyFormatter


@dataclass
class KeyRotationResult:
    """
    Result of a key rotation operation.

    Attributes:
        old_profile: The original security profile
        new_profile: The new security profile with fresh keys
        rotation_id: Timestamp-based identifier for this rotation
        legacy_key: Dictionary containing old keys (if keep_old_keys=True)
    """

    old_profile: SecurityProfile
    new_profile: SecurityProfile
    rotation_id: str
    legacy_key: Optional[dict] = None


class KeyRotator:
    """
    Manage key rotation for DLMS/COSEM security profiles.

    Key rotation is the process of replacing existing keys with new ones
    while optionally maintaining access to old keys for decrypting historical data.
    """

    @staticmethod
    def rotate(
        profile: SecurityProfile,
        new_suite: Optional[int] = None,
        keep_old_keys: bool = False,
        same_key: bool = True,
    ) -> KeyRotationResult:
        """
        Rotate keys in a security profile.

        Generates new encryption and authentication keys. Optionally saves
        the old keys for backward compatibility.

        Args:
            profile: Current security profile
            new_suite: New security suite (None to keep current)
            keep_old_keys: Whether to preserve old keys in the result
            same_key: Whether to use same key for encryption and authentication

        Returns:
            KeyRotationResult with old and new profiles

        Example:
            >>> result = KeyRotator.rotate(profile, keep_old_keys=True)
            >>> # Save result.new_profile to your configuration
            >>> # Store result.legacy_key for decrypting old data
        """
        from dataclasses import replace

        rotation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_suite = new_suite or profile.suite

        # Generate new keys
        new_key_pair = KeyGenerator.generate_key_pair(new_suite, same_key)

        # Create new profile with same metadata but new keys
        new_profile = replace(
            profile,
            suite=new_suite,
            encryption_key=new_key_pair.encryption_key,
            authentication_key=new_key_pair.authentication_key,
        )

        # Optionally preserve old keys
        legacy_key = None
        if keep_old_keys:
            legacy_key = {
                "encryption_key": KeyFormatter.format_key(
                    profile.encryption_key, "hex"
                ),
                "authentication_key": KeyFormatter.format_key(
                    profile.authentication_key, "hex"
                ),
                "rotated_at": datetime.now().isoformat(),
                "suite": profile.suite,
            }

        return KeyRotationResult(
            old_profile=profile,
            new_profile=new_profile,
            rotation_id=rotation_id,
            legacy_key=legacy_key,
        )

    @staticmethod
    def rotate_and_save(
        profile: SecurityProfile,
        output_path: str,
        new_suite: Optional[int] = None,
        keep_old_keys: bool = False,
    ) -> KeyRotationResult:
        """
        Rotate keys and save the new profile to a file.

        Args:
            profile: Current security profile
            output_path: Path to save the rotated configuration
            new_suite: New security suite (None to keep current)
            keep_old_keys: Whether to save old keys in the file

        Returns:
            KeyRotationResult with the new profile
        """
        result = KeyRotator.rotate(profile, new_suite, keep_old_keys)

        # Save the new profile
        from dlms_cosem.security.key_manager import KeyManager

        KeyManager.save(result.new_profile, output_path)

        return result
```

**Step 4: Run tests**

Run: `pytest tests/test_security/test_key_rotator.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add dlms_cosem/security/key_rotator.py tests/test_security/test_key_rotator.py
git commit -m "feat: implement KeyRotator for key rotation"
```

---

## Task 9: Create CLI Tool

**Files:**
- Create: `scripts/dlms-keys`
- Make executable: `chmod +x scripts/dlms-keys`

**Step 1: Write the CLI implementation**

```python
#!/usr/bin/env python
"""
dlms-keys - DLMS/COSEM Key Management CLI

Usage:
    dlms-keys generate [--suite SUITE] [--output FILE] [--profile NAME]
    dlms-keys validate [--file FILE] [--profile NAME]
    dlms-keys rotate [--file FILE] [--profile NAME] [--new-suite SUITE] [--keep-backup]
    dlms-keys convert [--input FILE] [--output FILE] [--format FORMAT]
    dlms-keys show [--profile NAME] [--file FILE]
    dlms-keys check-env
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dlms_cosem.security import (
    KeyManager,
    KeyRotator,
    KeyFormatter,
    KeyFormat,
    ConfigurationNotFoundError,
)


def cmd_generate(args):
    """Generate new keys and save to file."""
    print(f"Generating keys for Security Suite {args.suite}...")

    profile = KeyManager.generate(
        suite=args.suite,
        name=args.profile or "default",
    )

    if args.output:
        KeyManager.save(profile, args.output)
        print(f"✓ Keys saved to {args.output}")
    else:
        # Display keys
        print(f"\n--- Generated Keys (Suite {args.suite}) ---")
        print(f"Encryption Key:    {KeyFormatter.format_key(profile.encryption_key, 'hex')}")
        print(f"Authentication Key: {KeyFormatter.format_key(profile.authentication_key, 'hex')}")
        print(f"System Title:       {profile.system_title.hex()}")
        print("\nWarning: Keys are displayed above. Use --output to save to a file.")


def cmd_validate(args):
    """Validate keys in a configuration file."""
    try:
        if args.file:
            profile = KeyManager.load(profile_name=args.profile, paths=[args.file])
        else:
            profile = KeyManager.load(profile_name=args.profile)

        profile.validate()
        print(f"✓ Security profile '{args.profile}' is valid")
        print(f"  Suite: {profile.suite}")
        print(f"  Authenticated: {profile.authenticated}")
        print(f"  Encrypted: {profile.encrypted}")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)


def cmd_rotate(args):
    """Rotate keys in a configuration file."""
    try:
        if args.file:
            old_profile = KeyManager.load(profile_name=args.profile, paths=[args.file])
        else:
            old_profile = KeyManager.load(profile_name=args.profile)

        print(f"Rotating keys for profile '{args.profile}'...")

        result = KeyRotator.rotate(
            old_profile,
            new_suite=args.new_suite,
            keep_old_keys=args.keep_backup,
        )

        if args.output:
            KeyManager.save(result.new_profile, args.output)
            print(f"✓ New keys saved to {args.output}")
        else:
            # Update the original file
            KeyManager.save(result.new_profile, args.file)
            print(f"✓ Keys rotated and saved to {args.file}")

        print(f"  Rotation ID: {result.rotation_id}")

        if result.legacy_key:
            print(f"  Old keys preserved (backup enabled)")

    except Exception as e:
        print(f"✗ Rotation failed: {e}")
        sys.exit(1)


def cmd_convert(args):
    """Convert configuration between formats."""
    # Load from input
    profile = KeyManager.load(profile_name=args.profile, paths=[args.input])

    # Save to output
    KeyManager.save(profile, args.output)
    print(f"✓ Converted {args.input} to {args.output}")


def cmd_show(args):
    """Show current security configuration."""
    try:
        if args.file:
            profile = KeyManager.load(profile_name=args.profile, paths=[args.file])
        else:
            profile = KeyManager.load(profile_name=args.profile)

        print(f"\n--- Security Profile: {profile.name} ---")
        print(f"Suite:           {profile.suite} ({'AES-256' if profile.suite == 2 else 'AES-128'})")
        print(f"Authenticated:    {profile.authenticated}")
        print(f"Encrypted:        {profile.encrypted}")
        print(f"System Title:     {profile.system_title.hex() if profile.system_title else '(not set)'}")
        print(f"\nKeys:")
        print(f"  Encryption:    {KeyFormatter.format_key(profile.encryption_key, 'hex')[:32]}...")
        print(f"  Authentication: {KeyFormatter.format_key(profile.authentication_key, 'hex')[:32]}...")

    except ConfigurationNotFoundError as e:
        print(f"✗ Configuration not found: {e}")
        sys.exit(1)


def cmd_check_env():
    """Check environment variables for DLMS configuration."""
    import os

    env_vars = {
        "DLMS_SECURITY_SUITE": os.getenv("DLMS_SECURITY_SUITE"),
        "DLMS_ENCRYPTION_KEY": os.getenv("DLMS_ENCRYPTION_KEY"),
        "DLMS_AUTHENTICATION_KEY": os.getenv("DLMS_AUTHENTICATION_KEY"),
        "DLMS_SYSTEM_TITLE": os.getenv("DLMS_SYSTEM_TITLE"),
        "DLMS_AUTHENTICATED": os.getenv("DLMS_AUTHENTICATED"),
        "DLMS_ENCRYPTED": os.getenv("DLMS_ENCRYPTED"),
    }

    missing = [k for k, v in env_vars.items() if v is None and k not in
               ("DLMS_SYSTEM_TITLE", "DLMS_AUTHENTICATED", "DLMS_ENCRYPTED")]

    if missing and not any(env_vars[k] for k in ["DLMS_SECURITY_SUITE", "DLMS_ENCRYPTION_KEY"]):
        print("✗ DLMS environment variables not set")
        print("\nRequired variables:")
        print("  DLMS_SECURITY_SUITE=0")
        print("  DLMS_ENCRYPTION_KEY=hex:...")
        print("  DLMS_AUTHENTICATION_KEY=hex:...")
        sys.exit(1)

    print("DLMS environment variables:")
    for k, v in env_vars.items():
        if v:
            display = v
            if "KEY" in k:
                display = v[:20] + "..." if len(v) > 20 else v
            print(f"  {k}={display}")

    # Try to load and validate
    try:
        profile = KeyManager.load()
        profile.validate()
        print("\n✓ Environment configuration is valid")
    except Exception as e:
        print(f"\n✗ Environment configuration error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="DLMS/COSEM Key Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate new keys")
    gen_parser.add_argument("--suite", type=int, default=0, choices=[0, 1, 2],
                           help="Security suite (default: 0)")
    gen_parser.add_argument("--output", "-o", help="Output file path")
    gen_parser.add_argument("--profile", "-p", default="default",
                           help="Profile name (default: default)")

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate key configuration")
    val_parser.add_argument("--file", "-f", help="Configuration file path")
    val_parser.add_argument("--profile", "-p", default="default",
                           help="Profile name to validate (default: default)")

    # rotate
    rot_parser = subparsers.add_parser("rotate", help="Rotate keys")
    rot_parser.add_argument("--file", "-f", required=True, help="Configuration file path")
    rot_parser.add_argument("--profile", "-p", default="default",
                           help="Profile name to rotate (default: default)")
    rot_parser.add_argument("--new-suite", type=int, choices=[0, 1, 2],
                           help="New security suite (default: keep current)")
    rot_parser.add_argument("--keep-backup", action="store_true",
                           help="Preserve old keys in output")
    rot_parser.add_argument("--output", "-o", help="Output file path (default: update input)")

    # convert
    conv_parser = subparsers.add_parser("convert", help="Convert between formats")
    conv_parser.add_argument("--input", "-i", required=True, help="Input file path")
    conv_parser.add_argument("--output", "-o", required=True, help="Output file path")
    conv_parser.add_argument("--profile", "-p", default="default",
                           help="Profile name (default: default)")

    # show
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    show_parser.add_argument("--file", "-f", help="Configuration file path")
    show_parser.add_argument("--profile", "-p", default="default",
                           help="Profile name (default: default)")

    # check-env
    subparsers.add_parser("check-env", help="Check environment variables")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "rotate":
        cmd_rotate(args)
    elif args.command == "convert":
        cmd_convert(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "check-env":
        cmd_check_env()


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x scripts/dlms-keys
```

**Step 3: Test CLI**

```bash
# Test generate
./scripts/dlms-keys generate --suite 0 --output /tmp/test_keys.toml

# Test show
./scripts/dlms-keys show --file /tmp/test_keys.toml

# Test validate
./scripts/dlms-keys validate --file /tmp/test_keys.toml
```

**Step 4: Commit**

```bash
git add scripts/dlms-keys
git commit -m "feat: add dlms-keys CLI tool"
```

---

## Task 10: Update pyproject.toml Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add optional dependencies**

```toml
[project.optional-dependencies]
keyring = ["keyring"]
yaml = ["pyyaml"]
toml = ["tomli", "tomli-w"]

# Full key management features
keys = ["dlms-cosem[keyring,yaml,toml]"]
```

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add optional dependencies for key management"
```

---

## Task 11: Run Full Test Suite

**Step 1: Run all tests**

```bash
pytest tests/test_security/ -v
```

**Step 2: Run entire test suite to ensure no regressions**

```bash
pytest
```

**Step 3: Fix any issues and commit**

```bash
git commit -am "test: fix issues found during integration testing"
```

---

## Task 12: Update Documentation

**Files:**
- Create: `docs/key_management.md`
- Update: `README.md` (add key management section)

**Step 1: Create key management documentation**

```markdown
# Key Management

The `dlms-cosem` library provides comprehensive key management utilities for DLMS/COSEM security.

## Quick Start

### Generate Keys

```python
from dlms_cosem.security import KeyManager

# Generate a new security profile
profile = KeyManager.generate(suite=0, name="my_meter")

# Save to file
KeyManager.save(profile, "keys.toml")
```

### Load Keys

```python
# Auto-detect and load (env vars, files, etc.)
profile = KeyManager.load()

# Load from specific file
profile = KeyManager.load(paths=["keys.toml"])
```

### Using Predefined Strategies

```python
# HLS-GMAC with Suite 0
profile = KeyManager.from_strategy(
    "hls-gmac",
    encryption_key=my_key,
    authentication_key=my_key,
)

# Create a connection with the profile
# (See connection examples)
```

## CLI Tool

```bash
# Generate keys
dlms-keys generate --suite 0 --output keys.toml

# Validate configuration
dlms-keys validate --file keys.toml

# Rotate keys
dlms-keys rotate --file keys.toml --keep-backup

# Show current configuration
dlms-keys show --file keys.toml

# Check environment variables
dlms-keys check-env
```

## Configuration Formats

### TOML (Recommended)

```toml
[default]
suite = 0
encryption_key = "hex:00112233445566778899AABBCCDDEEFF"
authentication_key = "hex:00112233445566778899AABBCCDDEEFF"
system_title = "MDMID000"
authenticated = true
encrypted = true
```

### YAML

```yaml
default:
  suite: 0
  encryption_key: hex:00112233445566778899AABBCCDDEEFF
  authentication_key: hex:00112233445566778899AABBCCDDEEFF
```

### Environment Variables

```bash
export DLMS_SECURITY_SUITE=0
export DLMS_ENCRYPTION_KEY=hex:00112233445566778899AABBCCDDEEFF
export DLMS_AUTHENTICATION_KEY=hex:00112233445566778899AABBCCDDEEFF
```

## Key Rotation

```python
from dlms_cosem.security import KeyRotator

result = KeyRotator.rotate(profile, keep_old_keys=True)

# Save the new configuration
KeyManager.save(result.new_profile, "keys.toml")

# Store legacy keys for decrypting old data
legacy = result.legacy_key
```
```

**Step 2: Update README**

Add a section about key management.

**Step 3: Commit**

```bash
git add docs/key_management.md README.md
git commit -m "docs: add key management documentation"
```

---

## Completion Checklist

- [ ] All modules created with tests
- [ ] All tests passing (90%+ coverage)
- [ ] CLI tool functional
- [ ] Documentation updated
- [ ] No regressions in existing tests
- [ ] Code formatted and linted
