"""
Key management utilities for DLMS/COSEM.

This package provides:
- Key generation for Security Suites 0/1/2
- Key storage backends (environment, files, keyring)
- Security profile management
- Key rotation utilities
"""

# Security suite definitions
from dlms_cosem.key_management.security_suite import (
    SecuritySuite,
    SecuritySuiteNumber,
)

# Key generation
from dlms_cosem.key_management.key_generator import (
    KeyGenerator,
    KeyPair,
)

# Format conversion
from dlms_cosem.key_management.formatters import (
    KeyFormat,
    KeyFormatter,
)

# Security profiles
from dlms_cosem.key_management.profiles import (
    SecurityProfile,
    SECURITY_STRATEGIES,
)

# Storage backends
from dlms_cosem.key_management.key_storage import (
    KeyStorage,
    EnvironmentStorage,
    FileStorage,
    ConfigurationNotFoundError,
)

# Key manager (unified entry point)
from dlms_cosem.key_management.key_manager import (
    KeyManager,
)

# Key rotation
from dlms_cosem.key_management.key_rotator import (
    KeyRotator,
    KeyRotationResult,
)

__all__ = [
    # Security suite
    "SecuritySuite",
    "SecuritySuiteNumber",
    # Key generation
    "KeyGenerator",
    "KeyPair",
    # Format conversion
    "KeyFormat",
    "KeyFormatter",
    # Security profiles
    "SecurityProfile",
    "SECURITY_STRATEGIES",
    # Storage
    "KeyStorage",
    "EnvironmentStorage",
    "FileStorage",
    "ConfigurationNotFoundError",
    # Key manager
    "KeyManager",
    # Key rotation
    "KeyRotator",
    "KeyRotationResult",
]
