# API Reference: Transport

Complete API reference for transport layers.

## Table of Contents

- [Transport Interface](#transport-interface)
- [TCP Transport](#tcp-transport)
- [UDP Transport](#udp-transport)
- [Serial Transport](#serial-transport)
- [TLS Transport](#tls-transport)
- [HDLC Transport](#hdlc-transport)

---

## Transport Interface

### IOInterface

```python
from dlms_cosem.io import IOInterface

class IOInterface(ABC):
    """Abstract I/O interface for DLMS transport."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """Write data to transport."""

    @abstractmethod
    def read(self) -> bytes:
        """Read data from transport."""
```

---

## TCP Transport

### BlockingTcpIO

```python
from dlms_cosem.transport.tcp import BlockingTcpIO

class BlockingTcpIO(IOInterface):
    """Blocking TCP I/O implementation."""
```

### Constructor

```python
def __init__(
    self,
    host: str,
    port: int,
    timeout: float = 10.0,
) -> None:
    """
    Initialize TCP I/O.

    Args:
        host: Target host
        port: Target port
        timeout: Socket timeout in seconds
    """
```

### Methods

#### connect()

```python
def connect(self) -> None:
    """Connect to TCP server."""
```

#### disconnect()

```python
def disconnect(self) -> None:
    """Disconnect from TCP server."""
```

#### write() / read()

Inherited from `IOInterface`.

---

## UDP Transport

### BlockingUdpIO

```python
from dlms_cosem.transport.udp import BlockingUdpIO

class BlockingUdpIO(IOInterface):
    """Blocking UDP I/O implementation."""
```

### Constructor

```python
def __init__(
    self,
    host: str,
    port: int,
    timeout: float = 10.0,
    bind_host: str = "0.0.0.0",
    bind_port: int = 0,
) -> None:
    """
    Initialize UDP I/O.

    Args:
        host: Target host
        port: Target port
        timeout: Socket timeout in seconds
        bind_host: Bind address
        bind_port: Bind port
    """
```

---

## Serial Transport

### BlockingSerialIO

```python
from dlms_cosem.transport.serial import BlockingSerialIO

class BlockingSerialIO(IOInterface):
    """Blocking serial I/O implementation."""
```

### Constructor

```python
def __init__(
    self,
    port: str,
    baudrate: int = 9600,
    bytesize: int = 8,
    parity: str = "N",
    stopbits: int = 1,
    timeout: float = 1.0,
) -> None:
    """
    Initialize serial I/O.

    Args:
        port: Serial port (e.g., "/dev/ttyUSB0")
        baudrate: Baud rate (default: 9600)
        bytesize: Data bits (default: 8)
        parity: Parity (N/E/O, default: N)
        stopbits: Stop bits (default: 1)
        timeout: Read timeout in seconds (default: 1.0)
    """
```

### Methods

#### open() / close()

```python
def open(self) -> None:
    """Open serial port."""

def close(self) -> None:
    """Close serial port."""
```

---

## TLS Transport

### TlsTransport

```python
from dlms_cosem.transport.tls import TlsTransport

class TlsTransport(IOInterface):
    """TLS transport over TCP."""
```

### Constructor

```python
def __init__(
    self,
    host: str,
    port: int,
    certificate: Optional[str] = None,
    private_key: Optional[str] = None,
    ca_cert: Optional[str] = None,
    verify: bool = True,
    timeout: float = 10.0,
) -> None:
    """
    Initialize TLS transport.

    Args:
        host: Target host
        port: Target port
        certificate: Client certificate (PEM file path)
        private_key: Private key (PEM file path)
        ca_cert: CA certificate (PEM file path)
        verify: Verify server certificate
        timeout: Socket timeout in seconds
    """
```

---

## HDLC Transport

### HdlcTransport

```python
from dlms_cosem.hdlc.connection import HdlcConnection, HdlcAddress

class HdlcTransport:
    """HDLC transport over any I/O."""
```

### Constructor

```python
def __init__(
    self,
    io: IOInterface,
    client_address: HdlcAddress,
    server_address: HdlcAddress,
    timeout: float = 10.0,
) -> None:
    """
    Initialize HDLC transport.

    Args:
        io: Underlying I/O implementation
        client_address: Client HDLC address
        server_address: Server HDLC address
        timeout: Request timeout in seconds
    """
```

### Methods

#### send()

```python
def send(self, data: bytes) -> bytes:
    """
    Send HDLC data and receive response.

    Args:
        data: Raw DLMS APDU bytes

    Returns:
        Response bytes

    Raises:
        DlmsConnectionError: Connection error
        DlmsTimeoutError: Timeout
    """
```

---

## Examples

### TCP Connection

```python
from dlms_cosem.transport.tcp import BlockingTcpIO
from dlms_cosem import DlmsConnection

io = BlockingTcpIO(host="192.168.1.100", port=4059)
conn = DlmsConnection(io=io)
```

### Serial Connection

```python
from dlms_cosem.transport.serial import BlockingSerialIO
from dlms_cosem import DlmsConnection

io = BlockingSerialIO(
    port="/dev/ttyUSB0",
    baudrate=9600,
    parity="E",
)
conn = DlmsConnection(io=io)
```

### TLS Connection

```python
from dlms_cosem.transport.tls import TlsTransport
from dlms_cosem import DlmsConnection

io = TlsTransport(
    host="192.168.1.100",
    port=4059,
    certificate="client.pem",
    private_key="client_key.pem",
    ca_cert="ca.pem",
)
conn = DlmsConnection(io=io)
```

### Custom Transport

```python
from dlms_cosem.io import IOInterface
from dlms_cosem import DlmsConnection

class CustomIO(IOInterface):
    def __init__(self):
        self.data = bytearray()

    def write(self, data: bytes) -> None:
        self.data.extend(data)

    def read(self) -> bytes:
        return bytes(self.data)

io = CustomIO()
conn = DlmsConnection(io=io)
```

---

## See Also

- [API Reference: Client](api_client.md)
- [API Reference: Server](api_server.md)
- [Design Principles](design_principles.md)
- [Troubleshooting](troubleshooting.md)
