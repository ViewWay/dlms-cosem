# Security Suites

Complete reference for DLMS/COSEM security suites.

## Table of Contents

- [Overview](#overview)
- [Suite Definitions](#suite-definitions)
- [Key Requirements](#key-requirements)
- [Usage Examples](#usage-examples)
- [Algorithm Details](#algorithm-details)

---

## Overview

DLMS/COSEM defines 6 security suites (0-5) for different authentication and encryption levels.

| Suite | Authentication | Encryption | Description |
|--------|----------------|------------|-------------|
| 0 | None | None | No security |
| 1 | LLS | None | Low-level security |
| 2 | HLS | None | High-level security (SHA-256) |
| 3 | HLS | AES-GCM | AES encryption |
| 4 | HLS | SM4-GMAC | Chinese standard (GMAC) |
| 5 | HLS | SM4-GCM | Chinese standard (GCM) |

---

## Suite Definitions

### Suite 0: No Security

```python
from dlms_cosem.security import SecurityConfig, SecuritySuite

config = SecurityConfig(suite=SecuritySuite.SUITE_0)
```

- No authentication
- No encryption
- Only for testing or trusted networks

---

### Suite 1: LLS (Low-Level Security)

```python
config = SecurityConfig(
    suite=SecuritySuite.SUITE_1,
    password="00000000",
)
```

- Password authentication (8 hex digits)
- No encryption
- Common for read-only access

---

### Suite 2: HLS-ISM (High-Level Security)

```python
from dlms_cosem.security import SecurityConfig, SecuritySuite

config = SecurityConfig(
    suite=SecuritySuite.SUITE_2,
    system_title=b"Meter001",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=0,
)
```

- HLS-ISM authentication (SHA-256)
- No encryption
- Challenge-response mechanism

---

### Suite 3: HLS-ISM + AES-GCM

```python
config = SecurityConfig(
    suite=SecuritySuite.SUITE_3,
    system_title=b"Meter001",
    encryption_key=b"16_bytes_encr____",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=0,
)
```

- HLS-ISM authentication
- AES-128-GCM encryption
- International standard

---

### Suite 4: HLS-ISM + SM4-GMAC

```python
config = SecurityConfig(
    suite=SecuritySuite.SUITE_4,
    system_title=b"Meter001",
    encryption_key=b"16_bytes_encr____",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=0,
)
```

- HLS-ISM authentication
- SM4-GMAC authentication
- Chinese national standard

---

### Suite 5: HLS-ISM + SM4-GCM

```python
config = SecurityConfig(
    suite=SecuritySuite.SUITE_5,
    system_title=b"Meter001",
    encryption_key=b"16_bytes_encr____",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=0,
)
```

- HLS-ISM authentication
- SM4-GCM encryption
- Chinese national standard
- **Most secure for Chinese meters**

---

## Key Requirements

### Key Lengths

| Suite | Encryption Key | Authentication Key |
|--------|----------------|-------------------|
| 0 | None | None |
| 1 | None | 8 hex digits (4 bytes) |
| 2 | None | 16 bytes |
| 3 | 16 bytes | 16 bytes |
| 4 | 16 bytes | 16 bytes |
| 5 | 16 bytes | 16 bytes |

### System Title

- **Required**: Suites 2-5
- **Length**: 1-16 bytes (8 octets recommended)
- **Format**: ASCII or binary identifier
- **Example**: `b"Meter001"`

### Invocation Counter

- **Required**: Suites 2-5
- **Range**: 0-2^32-1
- **Must**: Increment after each authenticated operation
- **Must**: Never repeat (replay attack prevention)

---

## Usage Examples

### Suite 1: Password Authentication

```python
from dlms_cosem import DlmsClient
from dlms_cosem.security import SecurityConfig, SecuritySuite

config = SecurityConfig(
    suite=SecuritySuite.SUITE_1,
    password="00000000",
)

client = DlmsClient(conn, security_config=config)
voltage = client.get(obis)
```

### Suite 5: SM4-GCM (Chinese Standard)

```python
from dlms_cosem import DlmsClient
from dlms_cosem.security import SecurityConfig, SecuritySuite

config = SecurityConfig(
    suite=SecuritySuite.SUITE_5,
    system_title=b"ChinaMeter001",
    encryption_key=b"16_byte_SM4_key",
    authentication_key=b"16_byte_auth_key",
    invocation_counter=0,
)

client = DlmsClient(conn, security_config=config)
voltage = client.get(obis)
```

### Increment Invocation Counter

```python
from dlms_cosem.security import SecurityConfig, SecuritySuite

# Load counter from persistent storage
counter = load_invocation_counter()

config = SecurityConfig(
    suite=SecuritySuite.SUITE_5,
    system_title=b"Meter001",
    encryption_key=b"16_bytes_encr____",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=counter,
)

client = DlmsClient(conn, security_config=config)

# After each operation
voltage = client.get(obis)
counter += 1
save_invocation_counter(counter)
```

---

## Algorithm Details

### AES-128-GCM (Suite 3)

- **Standard**: NIST SP 800-38D
- **Key Size**: 128 bits (16 bytes)
- **IV**: 12 bytes
- **Tag**: 16 bytes
- **Implementation**: `cryptography` library

### SM4-GMAC (Suite 4)

- **Standard**: GM/T 0002-2014
- **Key Size**: 128 bits (16 bytes)
- **IV**: 16 bytes
- **Tag**: 16 bytes
- **Implementation**: `gmssl` library

### SM4-GCM (Suite 5)

- **Standard**: GM/T 0002-2014 (GCM mode)
- **Key Size**: 128 bits (16 bytes)
- **IV**: 12 bytes
- **Tag**: 16 bytes
- **Implementation**: `gmssl` library

### HLS-ISM (Suites 2-5)

- **Standard**: DLMS UA Yellow Book
- **Hash**: SHA-256
- **Challenge**: 16 bytes
- **Response**: 32 bytes
- **Implementation**: Built-in

---

## Key Generation

### Generate AES Key

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

encryption_key = os.urandom(16)  # 128 bits
authentication_key = os.urandom(16)
```

### Generate SM4 Key

```python
from gmssl import sm4, func
import os

encryption_key = os.urandom(16)  # 128 bits
authentication_key = os.urandom(16)
```

### Generate System Title

```python
import os

# Recommended: 8 bytes (64-bit ID)
system_title = b"Meter001"  # Or os.urandom(8)
```

---

## Validation

### Check Key Length

```python
from dlms_cosem.security import validate_key_length

# Returns True if valid
is_valid = validate_key_length(
    security_suite=SecuritySuite.SUITE_5,
    key_type="encryption",
    key_length=16,
)
```

### Validate Security Config

```python
from dlms_cosem.security import validate_security_config

try:
    validate_security_config(config)
    print("Config is valid")
except SecurityConfigError as e:
    print(f"Config invalid: {e}")
```

---

## Security Considerations

### Key Storage

- Never hardcode keys in source code
- Use environment variables or key management systems
- Rotate keys regularly (recommended: quarterly)
- Use separate keys for authentication and encryption

### Replay Attacks

- Always increment invocation counter
- Never reuse counter values
- Store counter persistently
- Monitor for counter jumps (possible attack)

### Key Compromise

- Rotate all keys immediately if compromised
- Revoke system title if possible
- Notify all affected parties
- Audit logs for unauthorized access

---

## References

- [DLMS UA Yellow Book](https://www.dlms.com/)
- [GB/T 32918-2016](https://openstd.samr.gov.cn/)
- [NIST SP 800-38D](https://csrc.nist.gov/publications/detail/sp/800-38d/final)

---

## See Also

- [API Reference: Client](api_client.md)
- [Security Module Documentation](../dlms_cosem/security.py)
- [Troubleshooting](troubleshooting.md)
