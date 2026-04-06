# Troubleshooting

Common issues and their solutions.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Authentication Errors](#authentication-errors)
- [Timeout Issues](#timeout-issues)
- [Data Reading Issues](#data-reading-issues)
- [Performance Issues](#performance-issues)
- [Debugging Tips](#debugging-tips)

---

## Connection Issues

### Issue: Connection Refused

```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Possible Causes**:
1. Wrong IP address
2. Wrong port number
3. Meter is offline
4. Firewall blocking connection

**Solutions**:
```python
# 1. Verify IP and port
import socket
socket.create_connection(("192.168.1.100", 4059), timeout=5)

# 2. Ping meter
import subprocess
subprocess.run(["ping", "-c", "1", "192.168.1.100"])

# 3. Check firewall
# On macOS: System Preferences → Security → Firewall
# On Linux: sudo ufw status
```

---

### Issue: Connection Timeout

```
DlmsTimeoutError: Connection timeout
```

**Possible Causes**:
1. Network latency
2. Meter busy
3. Incorrect baud rate (serial)

**Solutions**:
```python
# 1. Increase timeout
from dlms_cosem import DlmsClient
conn = DlmsConnection(host="192.168.1.100", port=4059, timeout=30)
client = DlmsClient(conn, timeout=30)

# 2. For serial, check baud rate
# Common baud rates: 300, 600, 1200, 2400, 4800, 9600, 19200
```

---

## Authentication Errors

### Issue: Authentication Failed

```
DlmsProtocolError: Authentication failed: Invalid password
```

**Possible Causes**:
1. Wrong password
2. Wrong authentication level
3. Meter locked

**Solutions**:
```python
# 1. Try low authentication (no password)
client = DlmsClient(conn, authentication="low")

# 2. Verify password format
# Usually 8 hexadecimal digits
client = DlmsClient(conn, authentication="low", password="00000000")

# 3. Check meter documentation for correct authentication level
# Common values: "low", "high", "hls"
```

---

### Issue: Access Denied

```
DlmsProtocolError: Access denied: Read access not allowed
```

**Possible Causes**:
1. Insufficient privileges
2. Attribute is write-only
3. Meter in programming mode

**Solutions**:
```python
# 1. Use higher authentication level
client = DlmsClient(conn, authentication="high", password="12345678")

# 2. Check attribute access rights in meter documentation
# 3. Try read-only attributes first
```

---

## Timeout Issues

### Issue: Read Timeout

```
DlmsTimeoutError: Read timeout after 10 seconds
```

**Possible Causes**:
1. Large data transfer
2. Network congestion
3. Meter processing delay

**Solutions**:
```python
# 1. Increase timeout
client.get(obis, timeout=30)

# 2. Use block transfer for large data
client.get(
    obis,
    use_block_transfer=True,
    max_block_size=200,
    timeout=60,
)
```

---

### Issue: Request Timeout

```
DlmsTimeoutError: Request timeout
```

**Possible Causes**:
1. Meter not responding
2. Wrong HDLC address
3. Serial connection issue

**Solutions**:
```python
# 1. Verify HDLC addresses
# Client address: usually 16
# Server address: usually 1
conn = DlmsConnection(
    client_logical_address=16,
    server_logical_address=1,
)

# 2. For serial, check connection
# Ensure RX/TX not swapped
```

---

## Data Reading Issues

### Issue: Invalid Data Type

```
ValueError: Invalid data type for OBIS code
```

**Possible Causes**:
1. Wrong OBIS code format
2. Attribute doesn't exist
3. Meter firmware issue

**Solutions**:
```python
# 1. Verify OBIS code
from dlms_cosem.cosem.obis import Obis

obis = Obis(1, 0, 1, 8, 0, 255)  # Active energy

# 2. Parse from string
obis = Obis.from_string("1-0:1.8.0.255")

# 3. Check meter documentation for valid OBIS codes
```

---

### Issue: Attribute Not Found

```
AttributeError: Attribute ID 42 not found for IC003 Register
```

**Possible Causes**:
1. Wrong attribute ID
2. Attribute not implemented in meter
3. Meter firmware version

**Solutions**:
```python
# 1. Use IC003 Register standard attributes
# Attribute 2 = Current value
# Attribute 3 = scaler/unit
client.get(obis, attribute_id=2)

# 2. Read all attributes to see what's available
from dlms_cosem.cosem.base import CosemObject
for attr in obj.attributes:
    print(f"ID {attr.id}: {attr.name}")
```

---

### Issue: Data is None

```python
result = client.get(obis)
print(result)  # None
```

**Possible Causes**:
1. Meter returns null value
2. Attribute is optional
3. Read protection

**Solutions**:
```python
# 1. Handle None explicitly
result = client.get(obis)
if result is None:
    print("Attribute not available or null")

# 2. Check if attribute is optional in meter docs
```

---

## Performance Issues

### Issue: Slow Reads

**Symptom**: Reading 10 attributes takes > 5 seconds

**Possible Causes**:
1. Network latency
2. Serial baud rate low
3. Many small requests

**Solutions**:
```python
# 1. Use WITH_LIST for multiple reads
obis_list = [Obis(1, 0, 1, 8, 0, 255), ...]
results = client.get_with_list(obis_list)

# 2. Increase serial baud rate (if supported)
# Change from 9600 to 115200

# 3. Use block transfer for large data
client.get(large_obis, use_block_transfer=True)
```

---

### Issue: High Memory Usage

**Symptom**: Memory grows when reading large profile data

**Possible Causes**:
1. Not using streaming
2. Loading entire profile into memory

**Solutions**:
```python
# 1. Use selective access to read only needed columns
from dlms_cosem.cosem.selective_access import AccessDescriptor

access = AccessDescriptor(
    access_selection=[1, 2, 3],  # Only columns 1, 2, 3
    from_entry=0,
    to_entry=100,
)
client.get(obis, access_selection=access)

# 2. Process in batches
for i in range(0, total_entries, 100):
    batch = client.get(obis, access_selection=AccessDescriptor(..., from_entry=i))
    process(batch)
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all DLMS operations are logged
client.get(obis)
```

### Capture Network Traffic

```python
# Use Wireshark or tcpdump
# Filter: tcp.port == 4059

# Or add custom logging
class LoggingIO(IOInterface):
    def __init__(self, wrapped_io):
        self.wrapped = wrapped_io

    def write(self, data: bytes):
        print(f"[SEND] {data.hex()}")
        self.wrapped.write(data)

    def read(self) -> bytes:
        data = self.wrapped.read()
        print(f"[RECV] {data.hex()}")
        return data

conn = DlmsConnection(io=LoggingIO(tcp_io))
```

### Test with Known Working Meter

Always test your code against a known working meter first:

```python
# Test meter with verified configuration
TEST_METER = {
    "host": "192.168.1.100",
    "port": 4059,
    "password": "00000000",
    "auth": "low",
}

conn = DlmsConnection(**TEST_METER)
client = DlmsClient(conn, authentication=TEST_METER["auth"])
```

### Check Library Version

```python
import dlms_cosem
print(dlms_cosem.__version__)

# Ensure you have the latest version
# pip install --upgrade dlms-cosem
```

---

## Common Error Messages

| Error Message | Cause | Solution |
|---------------|--------|----------|
| `Connection refused` | Meter offline or wrong port | Check IP/port, ping meter |
| `Authentication failed` | Wrong password/auth level | Verify credentials |
| `Access denied` | Insufficient privileges | Use higher authentication |
| `Timeout` | Meter not responding | Check network, increase timeout |
| `Invalid OBIS` | Wrong OBIS format | Use `Obis()` constructor |
| `Attribute not found` | Attribute ID doesn't exist | Check meter docs |
| `Data type error` | Unexpected data format | Handle exceptions gracefully |

---

## Getting Help

If you still have issues:

1. **Check Documentation**: [API Reference](api_reference.md), [Examples](examples.md)
2. **Search Issues**: [GitHub Issues](https://github.com/ViewWay/dlms-cosem/issues)
3. **Create New Issue**: Include:
   - Library version (`dlms_cosem.__version__`)
   - Meter model/firmware
   - Code snippet
   - Error message/traceback
   - Steps to reproduce
4. **Join Community**: [DLMS/COSEM Forum](https://www.dlms.com/)
