# API Reference: Server

Complete API reference for `CosemServer` and `CosemObjectModel`.

## Table of Contents

- [CosemServer](#cosemserver)
- [CosemObjectModel](#cosemobjectmodel)
- [Creating Objects](#creating-objects)
- [Running Server](#running-server)

---

## CosemServer

### Class Definition

```python
from dlms_cosem.server import CosemServer, ServerConfig

class CosemServer:
    """COSEM server for simulating meters."""
```

### Constructor

```python
def __init__(
    self,
    model: CosemObjectModel,
    config: Optional[ServerConfig] = None,
) -> None:
    """
    Initialize COSEM server.

    Args:
        model: COSEM object model
        config: Server configuration (optional)
    """
```

### Methods

#### start()

```python
async def start(
    self,
    host: str = "0.0.0.0",
    port: int = 4059,
) -> None:
    """
    Start server.

    Args:
        host: Bind address
        port: Bind port

    Raises:
        OSError: Cannot bind to port
    """
```

#### stop()

```python
async def stop(self) -> None:
    """Stop server."""
```

---

## CosemObjectModel

### Class Definition

```python
from dlms_cosem.server import CosemObjectModel

class CosemObjectModel:
    """Model of COSEM objects."""
```

### Methods

#### add_object()

```python
def add_object(self, obj: CosemObject) -> None:
    """
    Add COSEM object to model.

    Args:
        obj: COSEM object instance

    Raises:
        ValueError: Object already exists
    """
```

#### get_object()

```python
def get_object(
    self,
    logical_name: Union[Obis, bytes],
) -> Optional[CosemObject]:
    """
    Get COSEM object by logical name.

    Args:
        logical_name: OBIS code

    Returns:
        COSEM object or None
    """
```

#### remove_object()

```python
def remove_object(self, logical_name: Union[Obis, bytes]) -> None:
    """Remove COSEM object."""
```

---

## Creating Objects

### Register Object

```python
from dlms_cosem.cosem.base import CosemObject
from dlms_cosem.cosem.obis import Obis

class MyRegister(CosemObject):
    def __init__(self, logical_name: Obis):
        super().__init__(logical_name=logical_name)
        self._value = 0

    def get_attribute(self, attr_id: int) -> Any:
        if attr_id == 2:
            return self._value
        raise AttributeError(f"Attribute {attr_id} not found")

    def set_attribute(self, attr_id: int, value: Any) -> None:
        if attr_id == 2:
            self._value = value
        else:
            raise AttributeError(f"Attribute {attr_id} not found")

# Create and add
register = MyRegister(Obis(1, 0, 1, 8, 0, 255))
model.add_object(register)
```

### Use Built-in IC Classes

```python
from dlms_cosem.cosem.C3_Register import Register

register = Register(Obis(1, 0, 1, 8, 0, 255))
register.scaler_unit = 0
register.value = 12345.6
model.add_object(register)
```

---

## Running Server

### Basic Server

```python
import asyncio
from dlms_cosem.server import CosemServer, CosemObjectModel
from dlms_cosem.cosem.C3_Register import Register
from dlms_cosem.cosem.obis import Obis

# Create model
model = CosemObjectModel()

# Add objects
register = Register(Obis(1, 0, 1, 8, 0, 255))
register.value = 12345.6
model.add_object(register)

# Create and start server
server = CosemServer(model)

async def main():
    await server.start(host="0.0.0.0", port=4059)
    print("Server running on port 4059")

asyncio.run(main())
```

### Server with Configuration

```python
from dlms_cosem.server import ServerConfig

config = ServerConfig(
    port=4059,
    max_clients=10,
    timeout=30,
)
server = CosemServer(model, config=config)
```

---

## Request Handlers

### Custom Handlers

```python
from dlms_cosem.server import RequestHandler

class CustomHandler(RequestHandler):
    async def handle(
        self,
        data: bytes,
        model: CosemObjectModel,
    ) -> bytes:
        # Process request
        return response_bytes

# Register handler
from dlms_cosem.server import DlmsRequestRouter

router = DlmsRequestRouter()
router.register_handler("get", CustomHandler())
```

---

## Examples

### Three-Phase Meter Server

```python
from dlms_cosem.server import create_three_phase_meter_server

server = create_three_phase_meter_server()
await server.start(port=4059)
```

### Custom Model

```python
from dlms_cosem.server import CosemServer, CosemObjectModel

model = CosemObjectModel()
# Add custom objects
server = CosemServer(model)
await server.start(port=4059)
```

---

## See Also

- [API Reference: Client](api_client.md)
- [API Reference: Transport](api_transport.md)
- [Examples](examples.md)
- [Design Principles](design_principles.md)
