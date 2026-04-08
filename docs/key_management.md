# Key Management

The `dlms-cosem` library provides comprehensive key management utilities for DLMS/COSEM security.

## Quick Start

### Generate Keys

```python
from dlms_cosem.key_management import KeyManager

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
from dlms_cosem.key_management import KeyRotator

result = KeyRotator.rotate(profile, keep_old_keys=True)

# Save the new configuration
KeyManager.save(result.new_profile, "keys.toml")

# Store legacy keys for decrypting old data
legacy = result.legacy_key
```

## Security Strategies

The library provides predefined security strategies for common use cases:

| Strategy | Suite | Authenticated | Encrypted | Description |
|----------|-------|---------------|-----------|-------------|
| `none` | 0 | No | No | No security |
| `lls` | 0 | Yes (LLS) | No | Low Level Security |
| `hls-gmac` | 0 | Yes (HLS-GMAC) | Yes | High Level Security with AES-128 |
| `hls-suite2` | 2 | Yes (HLS-GMAC) | Yes | High Level Security with AES-256 |

```python
from dlms_cosem.key_management import SECURITY_STRATEGIES

# Use a predefined strategy
profile = SECURITY_STRATEGIES["hls-gmac"]
```

## API Reference

### KeyManager

```python
KeyManager.generate(suite, name="generated", same_key=True, system_title=None) -> SecurityProfile
KeyManager.load(profile_name="default", paths=None) -> SecurityProfile
KeyManager.save(profile, path) -> None
KeyManager.from_strategy(strategy_name, **overrides) -> SecurityProfile
KeyManager.validate(profile) -> None
```

### KeyGenerator

```python
KeyGenerator.generate_key(suite) -> bytes
KeyGenerator.generate_key_pair(suite, same_key=True) -> KeyPair
KeyGenerator.generate_system_title(manufacturer_id="MDM") -> bytes
```

### KeyFormatter

```python
KeyFormatter.encode(key, format, uppercase=False) -> str
KeyFormatter.decode(data) -> bytes
KeyFormatter.format_key(key, format="hex", prefix=True) -> str
```

### KeyRotator

```python
KeyRotator.rotate(profile, new_suite=None, keep_old_keys=False, same_key=True) -> KeyRotationResult
KeyRotator.rotate_and_save(profile, output_path, new_suite=None, keep_old_keys=False) -> KeyRotationResult
```

## Installation

For full key management features, install with optional dependencies:

```bash
pip install dlms-cosem[keys]
# or
uv pip install dlms-cosem[keys]
```

This installs:
- `pyyaml` - for YAML configuration file support
- `tomli` / `tomli-w` - for TOML configuration file support
- `keyring` - for system keyring support (optional)
