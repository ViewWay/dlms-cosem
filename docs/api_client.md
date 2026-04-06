# API Reference: Client

Complete API reference for `DlmsClient` and `AsyncDlmsClient`.

## Table of Contents

- [DlmsClient](#dlmsclient)
- [AsyncDlmsClient](#asyncdlmsclient)
- [Connection](#connection)
- [Authentication](#authentication)

---

## DlmsClient

### Class Definition

```python
from dlms_cosem import DlmsClient

class DlmsClient:
    """Synchronous DLMS/COSEM client."""
```

### Constructor

```python
def __init__(
    self,
    connection: DlmsConnection,
    authentication: str = "low",
    password: Optional[str] = None,
    security_config: Optional[SecurityConfig] = None,
    timeout: float = 10.0,
) -> None:
    """
    Initialize DLMS client.

    Args:
        connection: DLMS connection instance
        authentication: Authentication level ("low", "high", "hls")
        password: Password for authentication (8 hex digits)
        security_config: Security configuration for encrypted connections
        timeout: Request timeout in seconds

    Raises:
        ValueError: Invalid authentication level
        DlmsConnectionError: Connection failed
    """
```

### Methods

#### get()

```python
def get(
    self,
    obis: Obis,
    attribute_id: int = 2,
    access_selection: Optional[AccessDescriptor] = None,
    use_block_transfer: bool = False,
    max_block_size: int = 200,
    timeout: Optional[float] = None,
) -> Any:
    """
    Read attribute value.

    Args:
        obis: OBIS code
        attribute_id: Attribute ID (default: 2)
        access_selection: Selective access descriptor
        use_block_transfer: Use block transfer for large data
        max_block_size: Maximum block size
        timeout: Override default timeout

    Returns:
        Attribute value

    Raises:
        DlmsProtocolError: Protocol error
        DlmsTimeoutError: Timeout
    """
```

#### get_with_list()

```python
def get_with_list(
    self,
    obis_list: List[Obis],
    timeout: Optional[float] = None,
) -> Dict[Obis, Any]:
    """
    Read multiple attributes in single request.

    Args:
        obis_list: List of OBIS codes
        timeout: Override default timeout

    Returns:
        Dictionary mapping OBIS codes to values

    Raises:
        DlmsProtocolError: Protocol error
        DlmsTimeoutError: Timeout
    """
```

#### set()

```python
def set(
    self,
    obis: Obis,
    value: Any,
    attribute_id: int = 2,
    timeout: Optional[float] = None,
) -> None:
    """
    Write attribute value.

    Args:
        obis: OBIS code
        value: Value to write
        attribute_id: Attribute ID (default: 2)
        timeout: Override default timeout

    Raises:
        DlmsProtocolError: Protocol error
        DlmsTimeoutError: Timeout
        DlmsSecurityError: Write access denied
    """
```

#### set_with_list()

```python
def set_with_list(
    self,
    data: Dict[Obis, Any],
    timeout: Optional[float] = None,
) -> None:
    """
    Write multiple attributes in single request.

    Args:
        data: Dictionary mapping OBIS codes to values
        timeout: Override default timeout

    Raises:
        DlmsProtocolError: Protocol error
        DlmsTimeoutError: Timeout
    """
```

#### action()

```python
def action(
    self,
    obis: Obis,
    method_id: int,
    parameters: Optional[bytes] = None,
    timeout: Optional[float] = None,
) -> Optional[bytes]:
    """
    Call COSEM method.

    Args:
        obis: OBIS code
        method_id: Method ID
        parameters: Method parameters
        timeout: Override default timeout

    Returns:
        Method result data (if any)

    Raises:
        DlmsProtocolError: Protocol error
        DlmsTimeoutError: Timeout
    """
```

#### close()

```python
def close(self) -> None:
    """Close connection."""
```

---

## AsyncDlmsClient

### Class Definition

```python
from dlms_cosem import AsyncDlmsClient

class AsyncDlmsClient:
    """Asynchronous DLMS/COSEM client."""
```

### Constructor

```python
def __init__(
    self,
    connection: AsyncDlmsConnection,
    authentication: str = "low",
    password: Optional[str] = None,
    security_config: Optional[SecurityConfig] = None,
    timeout: float = 10.0,
) -> None:
    """
    Initialize async DLMS client.

    Args:
        connection: Async DLMS connection instance
        authentication: Authentication level ("low", "high", "hls")
        password: Password for authentication
        security_config: Security configuration
        timeout: Request timeout in seconds
    """
```

### Methods

All methods are async versions of `DlmsClient` methods:

- `async get(...)` → `Awaitable[Any]`
- `async get_with_list(...)` → `Awaitable[Dict[Obis, Any]]`
- `async set(...)` → `Awaitable[None]`
- `async set_with_list(...)` → `Awaitable[None]`
- `async action(...)` → `Awaitable[Optional[bytes]]`
- `async close()` → `Awaitable[None]`

---

## Connection

### DlmsConnection

```python
from dlms_cosem import DlmsConnection

class DlmsConnection:
    """DLMS connection over TCP/UDP/Serial."""
```

### Constructor

```python
def __init__(
    self,
    host: str,
    port: int,
    client_logical_address: int = 16,
    server_logical_address: int = 1,
    timeout: float = 10.0,
) -> None:
    """
    Initialize DLMS connection.

    Args:
        host: Meter IP address
        port: Meter port (e.g., 4059)
        client_logical_address: Client HDLC address (default: 16)
        server_logical_address: Server HDLC address (default: 1)
        timeout: Connection timeout in seconds
    """
```

---

## Authentication

### Authentication Levels

| Level | Password Required | Description |
|--------|------------------|-------------|
| `low` | Optional | Low-level authentication |
| `high` | Required | High-level authentication |
| `hls` | Required | HLS-ISM authentication |

### Security Configuration

```python
from dlms_cosem.security import SecurityConfig, SecuritySuite

config = SecurityConfig(
    suite=SecuritySuite.SUITE_5,  # SM4-GCM
    system_title=b"Meter001",
    encryption_key=b"16_bytes_key____",
    authentication_key=b"16_bytes_auth___",
    invocation_counter=0,
)
```

---

## Examples

### Basic Read

```python
from dlms_cosem import DlmsClient, DlmsConnection
from dlms_cosem.cosem.obis import Obis

conn = DlmsConnection(host="192.168.1.100", port=4059)
client = DlmsClient(conn, authentication="low", password="00000000")

voltage = client.get(Obis(1, 0, 32, 7, 0, 255))
print(f"Voltage: {voltage} V")

conn.close()
```

### Async Read

```python
import asyncio
from dlms_cosem import AsyncDlmsClient, AsyncDlmsConnection
from dlms_cosem.cosem.obis import Obis

async def main():
    conn = await AsyncDlmsConnection.connect("192.168.1.100", 4059)
    client = AsyncDlmsClient(conn, authentication="low")
    voltage = await client.get(Obis(1, 0, 32, 7, 0, 255))
    await client.close()

asyncio.run(main())
```

---

## See Also

- [API Reference: Server](api_server.md)
- [API Reference: Transport](api_transport.md)
- [Examples](examples.md)
- [Troubleshooting](troubleshooting.md)
