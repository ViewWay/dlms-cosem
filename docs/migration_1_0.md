# Migration Guide: 0.x to 1.0

This guide helps you migrate from `dlms-cosem` 0.x to 1.0.

## Table of Contents

- [Breaking Changes](#breaking-changes)
- [Deprecated Features](#deprecated-features)
- [New Features](#new-features)
- [Migration Examples](#migration-examples)
- [Troubleshooting](#troubleshooting)

---

## Breaking Changes

### 1. Authentication API Changed

#### Before (0.x)

```python
client = DlmsClient(
    conn,
    authentication_password="00000000",
    authentication_level="low",
)
```

#### After (1.0)

```python
client = DlmsClient(
    conn,
    authentication="low",
    password="00000000",
)
```

**Reason**: Simplified API, clearer parameter names.

---

### 2. Error Handling Changed

#### Before (0.x)

```python
try:
    client.get(obis)
except Exception as e:
    print(f"Error: {e}")
```

#### After (1.0)

```python
from dlms_cosem.exceptions import (
    DlmsProtocolError,
    DlmsConnectionError,
    DlmsTimeoutError,
)

try:
    client.get(obis)
except DlmsProtocolError as e:
    print(f"Protocol error: {e}")
except DlmsConnectionError as e:
    print(f"Connection error: {e}")
except DlmsTimeoutError as e:
    print(f"Timeout: {e}")
```

**Reason**: Better error handling with specific exception types.

---

### 3. OBIS Code Construction

#### Before (0.x)

```python
obis = Obis("1-0:1.8.0.255")
```

#### After (1.0)

```python
from dlms_cosem.cosem.obis import Obis

obis = Obis(1, 0, 1, 8, 0, 255)

# String parsing still works
obis = Obis.from_string("1-0:1.8.0.255")
```

**Reason**: Type-safe OBIS construction, explicit integer parameters.

---

### 4. HDLC Connection API

#### Before (0.x)

```python
conn = HdlcConnection(
    io=tcp_io,
    client_address=16,
    server_address=1,
    use_window=True,
)
```

#### After (1.0)

```python
from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.hdlc.connection import HdlcConnection

client = HdlcAddress(logical_address=16, address_type="client")
server = HdlcAddress(logical_address=1, address_type="server")

conn = HdlcConnection(
    io=tcp_io,
    client_address=client,
    server_address=server,
)
```

**Reason**: Better address abstraction, type-safe.

---

### 5. Block Transfer API

#### Before (0.x)

```python
data = client.get(obis, block_transfer=True)
```

#### After (1.0)

```python
data = client.get(
    obis,
    use_block_transfer=True,
    max_block_size=200,
)
```

**Reason**: More explicit control over block transfer parameters.

---

## Deprecated Features

### `authentication_level` Parameter

Use `authentication` instead:

```python
# Deprecated
client = DlmsClient(conn, authentication_level="low", ...)

# New
client = DlmsClient(conn, authentication="low", ...)
```

### `HdlcConnection.use_window`

Window mechanism is now automatic:

```python
# Deprecated
conn = HdlcConnection(io, use_window=True)

# New (automatic)
conn = HdlcConnection(io)
```

---

## New Features

### 1. Async Client

```python
from dlms_cosem import AsyncDlmsClient, AsyncDlmsConnection
import asyncio

async def read_meter():
    conn = await AsyncDlmsConnection.connect(
        host="192.168.1.100",
        port=4059,
    )
    client = AsyncDlmsClient(conn, authentication="low")
    voltage = await client.get(Obis(1, 0, 32, 7, 0, 255))
    await client.close()

asyncio.run(read_meter())
```

### 2. WebSocket Gateway

```python
from dlms_cosem.ws_gateway import WsGateway

gateway = WsGateway(
    host="0.0.0.0",
    port=8765,
    dlms_host="192.168.1.100",
    dlms_port=4059,
)
gateway.run()
```

### 3. Enhanced Security

```python
from dlms_cosem.security import SecurityConfig

config = SecurityConfig(
    suite=SecuritySuite.SUITE_5,  # SM4-GCM
    system_title=b"Meter001",
    encryption_key=b"16_bytes_key____",
    authentication_key=b"16_bytes_auth___",
)
client = DlmsClient(conn, security_config=config)
```

---

## Migration Examples

### Example 1: Basic Read

#### Before (0.x)

```python
from dlms_cosem import DlmsClient, DlmsConnection

conn = DlmsConnection("192.168.1.100", 4059, 16, 1)
client = DlmsClient(
    conn,
    authentication_password="00000000",
    authentication_level="low",
)
voltage = client.get("1-0:32.7.0.255")
```

#### After (1.0)

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="low", password="00000000")
voltage = client.get(Obis(1, 0, 32, 7, 0, 255))
```

---

### Example 2: Set Attribute

#### Before (0.x)

```python
client.set("1-0:19.0.0.255", 1)
```

#### After (1.0)

```python
client.set(Obis(1, 0, 19, 0, 0, 255), 1)
```

---

### Example 3: HDLC Connection

#### Before (0.x)

```python
conn = HdlcConnection(io, client_address=16, server_address=1)
```

#### After (1.0)

```python
from dlms_cosem.hdlc.address import HdlcAddress

client = HdlcAddress(logical_address=16, address_type="client")
server = HdlcAddress(logical_address=1, address_type="server")
conn = HdlcConnection(io=io, client_address=client, server_address=server)
```

---

## Troubleshooting

### Issue: `TypeError: 'Obis' object is not callable`

**Cause**: Using old OBIS string format.

**Solution**:
```python
# Wrong
obis = Obis("1-0:1.8.0.255")

# Correct
obis = Obis.from_string("1-0:1.8.0.255")
# Or
obis = Obis(1, 0, 1, 8, 0, 255)
```

### Issue: `AttributeError: 'DlmsClient' has no attribute 'authentication_level'`

**Cause**: Old parameter name.

**Solution**: Use `authentication` instead.

### Issue: ImportError after upgrade

**Cause**: Module reorganization.

**Solution**: Reinstall dependencies:
```bash
uv pip install --upgrade dlms-cosem
```

---

## Need Help?

- [API Reference](api_reference.md) — Complete API documentation
- [Examples](examples.md) — Code examples
- [GitHub Issues](https://github.com/ViewWay/dlms-cosem/issues) — Report problems
