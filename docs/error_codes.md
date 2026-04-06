# Error Codes

This document lists all error codes and their meanings.

## Table of Contents

- [DLMS Protocol Errors](#dlms-protocol-errors)
- [Security Errors](#security-errors)
- [Connection Errors](#connection-errors)
- [Timeout Errors](#timeout-errors)

---

## DLMS Protocol Errors

### Service Errors (0x01 - 0xFF)

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| 0x01 | `SERVICE_NOT_SUPPORTED` | Service is not supported by the meter | Check meter capabilities, use supported service |
| 0x02 | `SERVICE_UNKNOWN` | Service ID is unknown | Verify APDU structure |
| 0x03 | `APPLICATION_REFERENCE_NAME_INVALID` | Invalid COSEM object reference | Check OBIS code |
| 0x04 | `HARDWARE_FAULT` | Hardware fault in meter | Contact meter manufacturer |
| 0x05 | `TEMPORARILY_UNAVAILABLE` | Service temporarily unavailable | Retry later |
| 0x06 | `OBJECT_UNDEFINED` | COSEM object doesn't exist | Check OBIS code, IC class support |
| 0x07 | `OBJECT_CLASS_INCONSISTENT` | Object class doesn't match logical name | Check OBIS vs IC class |
| 0x08 | `OBJECT_UNAVAILABLE` | Object is not accessible | Check object availability |
| 0x09 | `TYPE_UNRECOGNIZED` | Data type not recognized | Check data type in IC class |
| 0x0A | `ACCESS_DENIED` | Access denied | Check authentication level |
| 0x0B | `GET_RESPONSE_UNAVAILABLE` | Get response not available | Use other read method |
| 0x0C | `SET_RESPONSE_UNAVAILABLE` | Set response not available | Check write access |
| 0x0D | `ACTION_RESPONSE_UNAVAILABLE` | Action response not available | Check method availability |
| 0x0E | `BLOCK_NUMBER_UNAVAILABLE` | Block transfer number unavailable | Check block transfer state |
| 0x0F | `BLOCK_NUMBER_INVALID` | Invalid block number | Verify block number |
| 0x10 | `READ_WRITE_DENIED` | Read/write access denied | Check object access rights |
| 0x11 | `BLOCK_UNAVAILABLE` | Block transfer data unavailable | Retry block transfer |
| 0x12 | `BLOCK_ALREADY_SENT` | Block already sent | Check duplicate blocks |
| 0x13 | `DATA_BLOCK_UNAVAILABLE` | Data block unavailable | Check buffer status |

### Data Access Errors (0x20 - 0x2F)

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| 0x20 | `READ_WRITE_DENIED` | Read or write access denied | Check authentication level |
| 0x21 | `OBJECT_ACCESS_DENIED` | Object access denied | Check object access rights |
| 0x22 | `SELECTIVE_ACCESS_DENIED` | Selective access not allowed | Use normal access |
| 0x23 | `PARAMETER_OUT_OF_RANGE` | Parameter value out of range | Check parameter limits |
| 0x24 | `PARAMETER_UNEXPECTED` | Unexpected parameter value | Check parameter type |
| 0x25 | `DATA_UNAVAILABLE` | Data not available | Check if data exists |
| 0x26 | `TIMEOUT` | Operation timeout | Increase timeout |

---

## Security Errors

### Security Suite Errors

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| `SECURITY_SUITE_INVALID` | Invalid security suite | Check suite number (0-5) |
| `KEY_LENGTH_INVALID` | Invalid key length | Use correct key length (16/24/32 bytes) |
| `AUTHENTICATION_FAILED` | Authentication failed | Check password/credentials |
| `ENCRYPTION_FAILED` | Encryption failed | Check encryption key |
| `DECRYPTION_FAILED` | Decryption failed | Check decryption key |
| `SIGNATURE_INVALID` | Invalid signature | Verify signature |
| `CIPHER_MISMATCH` | Cipher mismatch | Check cipher suite |

### HLS-ISM Errors

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| `HLS_CHALLENGE_FAILED` | HLS challenge failed | Check challenge response |
| `HLS_SIGNATURE_FAILED` | HLS signature failed | Check signature calculation |
| `HLS_COUNTER_INVALID` | Invocation counter invalid | Check counter value |

---

## Connection Errors

### HDLC Errors

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| `CONNECTION_REFUSED` | Connection refused | Check IP/port, ping meter |
| `CONNECTION_RESET` | Connection reset | Check network stability |
| `CONNECTION_TIMEOUT` | Connection timeout | Increase timeout, check network |
| `INVALID_ADDRESS` | Invalid HDLC address | Check client/server addresses |
| `FRAME_CRC_ERROR` | Frame CRC error | Check cable, reduce noise |
| `FRAME_LENGTH_ERROR` | Frame length error | Check frame format |
| `INVALID_SEQUENCE` | Invalid frame sequence | Check sliding window |

---

## Timeout Errors

| Error Code | Name | Description | Solution |
|------------|------|-------------|-----------|
| `RESPONSE_TIMEOUT` | Response timeout | Increase timeout |
| `REQUEST_TIMEOUT` | Request timeout | Check network, meter availability |
| `BLOCK_TRANSFER_TIMEOUT` | Block transfer timeout | Check block transfer settings |
| `KEEP_ALIVE_TIMEOUT` | Keep-alive timeout | Adjust keep-alive interval |

---

## Python Exceptions

### DlmsException Hierarchy

```
DlmsException (base)
├── DlmsProtocolError
│   ├── ServiceError
│   ├── DataAccessError
│   └── SecurityError
├── DlmsConnectionError
│   ├── ConnectionRefusedError
│   ├── ConnectionResetError
│   └── ConnectionTimeoutError
├── DlmsTimeoutError
└── DlmsSecurityError
    ├── AuthenticationError
    ├── EncryptionError
    └── SignatureError
```

### Example Handling

```python
from dlms_cosem.exceptions import (
    DlmsException,
    DlmsProtocolError,
    DlmsConnectionError,
    DlmsTimeoutError,
    ServiceError,
    DataAccessError,
)

try:
    client.get(obis)
except ServiceError as e:
    print(f"Service error: {e.error_code} - {e.message}")
except DataAccessError as e:
    print(f"Data access error: {e.error_code} - {e.message}")
except DlmsConnectionError as e:
    print(f"Connection error: {e}")
except DlmsTimeoutError as e:
    print(f"Timeout: {e}")
except DlmsProtocolError as e:
    print(f"Protocol error: {e}")
except DlmsException as e:
    print(f"DLMS error: {e}")
```

---

## Getting Help

If you encounter an error not listed here:

1. **Check Error Details**: Use `repr(e)` for full error info
2. **Search Documentation**: [API Reference](api_reference.md), [Troubleshooting](troubleshooting.md)
3. **Report Issue**: [GitHub Issues](https://github.com/ViewWay/dlms-cosem/issues)
