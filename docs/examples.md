# Examples

This page provides code examples for common DLMS/COSEM operations.

## Table of Contents

- [Basic Read Operations](#basic-read-operations)
- [Setting Attributes](#setting-attributes)
- [Calling Methods](#calling-methods)
- [Block Transfer](#block-transfer)
- [With List Operations](#with-list-operations)
- [Async Client](#async-client)
- [WebSocket Gateway](#websocket-gateway)
- [Custom IC Classes](#custom-ic-classes)

---

## Basic Read Operations

### Read a Single Register

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

# Connect to meter
conn = DlmsConnection(
    host="192.168.1.100",
    port=4059,
    client_logical_address=16,
    server_logical_address=1,
)
client = DlmsClient(conn, authentication="low", password="00000000")

# Read voltage (1-0:32.7.0.255)
voltage = client.get(Obis(1, 0, 32, 7, 0, 255))
print(f"Voltage: {voltage} V")

conn.close()
```

### Read Multiple Registers (WITH_LIST)

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="low", password="00000000")

# Read multiple attributes in single request
obis_list = [
    Obis(1, 0, 1, 8, 0, 255),   # Active energy
    Obis(1, 0, 32, 7, 0, 255),  # Voltage
    Obis(1, 0, 31, 7, 0, 255),  # Current
]

results = client.get_with_list(obis_list)
for obis, value in results.items():
    print(f"{obis}: {value}")

conn.close()
```

---

## Setting Attributes

### Set Register Value

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="high", password="12345678")

# Set relay status (1-0:19.0.0.255)
client.set(Obis(1, 0, 19, 0, 0, 255), 1)  # 1 = ON

conn.close()
```

---

## Calling Methods

### Trigger Method

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="high", password="12345678")

# Reset method on IC001 Data (1-0:0.0.0.255, method 1)
result = client.action(Obis(1, 0, 0, 0, 0, 255), 1)
print(f"Method result: {result}")

conn.close()
```

---

## Block Transfer

### Read Large Profile Data with Block Transfer

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="low", password="00000000")

# Read load profile (1-0:99.1.0.255) with block transfer
profile_data = client.get(
    Obis(1, 0, 99, 1, 0, 255),
    use_block_transfer=True,
    max_block_size=200,
)

print(f"Profile entries: {len(profile_data)}")

conn.close()
```

---

## With List Operations

### Set Multiple Attributes

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="high", password="12345678")

# Set multiple attributes in single request
data = {
    Obis(1, 0, 19, 0, 0, 255): 1,  # Relay status
    Obis(1, 0, 14, 0, 0, 255): 100,  # Threshold
}

client.set_with_list(data)

conn.close()
```

---

## Async Client

### Async Read Operations

```python
import asyncio
from dlms_cosem import AsyncDlmsClient, AsyncDlmsConnection
from dlms_cosem.cosem.obis import Obis

async def read_meter():
    # Connect to meter
    conn = await AsyncDlmsConnection.connect(
        host="192.168.1.100",
        port=4059,
        client_logical_address=16,
        server_logical_address=1,
    )
    client = AsyncDlmsClient(conn, authentication="low", password="00000000")

    # Read voltage
    voltage = await client.get(Obis(1, 0, 32, 7, 0, 255))
    print(f"Voltage: {voltage} V")

    # Close connection
    await client.close()

# Run async function
asyncio.run(read_meter())
```

---

## WebSocket Gateway

### Connect via WebSocket

```python
import websockets
import asyncio
import json

async def websocket_client():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as ws:
        # Send DLMS request
        request = {
            "action": "get",
            "obis": "1-0:1.8.0.255",
            "authentication": {"method": "low", "password": "00000000"}
        }
        await ws.send(json.dumps(request))

        # Receive response
        response = await ws.recv()
        result = json.loads(response)
        print(f"Result: {result['data']}")

asyncio.run(websocket_client())
```

---

## Custom IC Classes

### Create Custom IC Class

```python
from dlms_cosem.cosem.base import CosemObject
from dlms_cosem.cosem.obis import Obis

class MyCustomIC(CosemObject):
    """Custom IC class example"""

    def __init__(self, logical_name: Obis):
        super().__init__(logical_name=logical_name)
        self.attribute_1 = 0

    # Implement abstract methods
    def get_attribute(self, attr_id: int):
        if attr_id == 1:
            return self.attribute_1
        raise AttributeError(f"Attribute {attr_id} not found")

    def set_attribute(self, attr_id: int, value):
        if attr_id == 1:
            self.attribute_1 = value
        else:
            raise AttributeError(f"Attribute {attr_id} not found")

# Register with factory
from dlms_cosem.cosem.factory import CosemObjectFactory
CosemObjectFactory.register(999, MyCustomIC)
```

---

## Error Handling

### Handle Exceptions

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.exceptions import (
    DlmsConnectionError,
    DlmsProtocolError,
    DlmsTimeoutError,
)

try:
    conn = DlmsConnection(host="192.168.1.100", port=4059)
    client = DlmsClient(conn, authentication="low", password="00000000")

    voltage = client.get(Obis(1, 0, 32, 7, 0, 255))
    print(f"Voltage: {voltage} V")

    conn.close()

except DlmsConnectionError as e:
    print(f"Connection failed: {e}")
except DlmsProtocolError as e:
    print(f"Protocol error: {e}")
except DlmsTimeoutError as e:
    print(f"Timeout: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Next Steps

- [API Reference](api_reference.md) — Complete API documentation
- [Architecture](ARCHITECTURE.md) — Design principles and architecture
- [Troubleshooting](troubleshooting.md) — Common issues and solutions
