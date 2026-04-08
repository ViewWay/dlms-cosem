# DLMS/COSEM API Reference

## Core Modules

### `dlms_cosem.client` — DlmsClient

Main client for communicating with DLMS meters.

```python
from dlms_cosem.client import DlmsClient

client = DlmsClient(
    client_logical_name="DLMS",
    server_logical_name="METER",
    server_physical_address=1,
    authentication_key=b"...",
    encryption_key=b"...",
)
```

### `dlms_cosem.connection` — Connection Management

```python
from dlms_cosem.connection import DlmsConnection
```

### `dlms_cosem.cosem` — COSEM Interface Classes

All COSEM IC classes follow a consistent pattern:

```python
from dlms_cosem.cosem.register import Register
from dlms_cosem.cosem.obis import Obis

register = Register(Obis(0, 0, 1, 0, 0, 255))
```

#### Available IC Classes

| Class | Module | class_id |
|-------|--------|----------|
| Data | `cosem.data` | 1 |
| Register | `cosem.register` | 3 |
| Extended Register | `cosem.extended_register` | 4 |
| Demand Register | `cosem.demand_register` | 5 |
| Register Activation | `cosem.register_activation` | 6 |
| Profile Generic | `cosem.profile_generic` | 7 |
| Clock | `cosem.clock` | 8 |
| Script Table | `cosem.script_table` | 9 |
| Schedule | `cosem.action_schedule` | 10 |
| Special Days Table | `cosem.special_day_table` | 11 |
| Association SN | `cosem.association_sn` | 12 |
| Security Setup | `cosem.security_setup` | 64 |
| Image Transfer | `cosem.image_transfer` | 68 |

### `dlms_cosem.cosem.obis` — OBIS Codes

```python
from dlms_cosem.cosem.obis import Obis

obis = Obis(0, 0, 1, 0, 0, 255)  # Active energy+
obis = Obis.from_str("0.0.1.0.0.255")
data = obis.to_bytes()  # 6 bytes
```

### `dlms_cosem.cosem.factory` — Object Factory

```python
from dlms_cosem.cosem.factory import create_cosem_object
from dlms_cosem.cosem.obis import Obis

obj = create_cosem_object(class_id=3, logical_name=Obis(0, 0, 1, 0, 0, 255))
```

### `dlms_cosem.hdlc` — HDLC Framing

```python
from dlms_cosem.hdlc.frames import IFrame, SFrame, UFrame
from dlms_cosem.hdlc.address import HdlcAddress

frame = IFrame.from_bytes(data)
```

### `dlms_cosem.a_xdr` — A-XDR Encoding/Decoding

```python
from dlms_cosem import a_xdr

# Encoding
data = a_xdr.encoding.long_unsigned_en(0, 1000)
data = a_xdr.encoding.octet_string_en(0, b"\x01\x02\x03")

# Decoding
value, index = a_xdr.decoding.long_unsigned(data, 0)
```

### `dlms_cosem.dlms_data` — DLMS Data Types

```python
from dlms_cosem.dlms_data import Data, Integer, Structure, Array

parsed = Data.from_bytes(raw_bytes)
```

#### Data Types

- `Integer`, `LongUnsigned`, `Unsigned`
- `OctetString`, `String`, `Utf8String`
- `Boolean`, `Float`, `Double`
- `Structure`, `Array`, `CompactArray`
- `BitString`, `Enum`, `DateTime`, `NoneType`

### `dlms_cosem.security` — Security

```python
from dlms_cosem.security import SM4Cipher

cipher = SM4Cipher(key=b"\x00" * 16, nonce=b"\x00" * 12)
ciphertext = cipher.encrypt(plaintext)
plaintext = cipher.decrypt(ciphertext)
```

### `dlms_cosem.exceptions` — Exception Hierarchy

```python
from dlms_cosem.exceptions import (
    DlmsException,          # Base exception
    DlmsProtocolError,      # Protocol errors
    DlmsSecurityError,      # Security errors
    DlmsConnectionError,    # Connection errors
    DlmsClientError,        # Client errors
    DlmsDataError,          # Data errors
)
```

### `dlms_cosem.transport` — Transport Layers

- `nbiot` — NB-IoT transport
- `tls` — TLS transport
- `lorawan` — LoRaWAN transport

### `dlms_cosem.protocol` — Protocol Layer

- `xdlms` — xDLMS APDU handling (Get, Set, Action, Initiate, etc.)
- `acse` — ACSE association (AARQ, AARE, RLRQ, RLRE)
- `wrappers` — APDU wrappers

### `dlms_cosem.server` — COSEM Server

```python
from dlms_cosem.server import CosemServer
```

### `dlms_cosem.automation` — Automation

```python
from dlms_cosem.automation import MeterAutomation
```

### `dlms_cosem.ws_gateway` — WebSocket Gateway

```python
from dlms_cosem.ws_gateway import WsGateway
```

### `dlms_cosem.key_management` — Key Management

```python
from dlms_cosem.key_management import KeyManager, SecuritySuite
```

### `dlms_cosem.parsers` — Data Parsers

```python
from dlms_cosem.parsers import ProfileGenericParser, AssociationSnParser
```
