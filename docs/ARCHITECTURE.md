# DLMS/COSEM Library Architecture

This document describes the architecture and design of the DLMS/COSEM Python library.

## Overview

The library implements the DLMS/COSEM (Device Language Message Specification / Companion Specification for Energy Metering) protocol for communication with smart meters and other energy measuring devices.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ DlmsClient   │  │   Examples    │  │    User      │       │
│  └──────┬───────┘  └──────────────┘  └──────────────┘       │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                      Client Interface Layer                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  get() | get_with_range() | get_with_entry() | set()    │   │
│  │  action() | associate() | disconnect()                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                      Connection Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  DlmsConnection                                           │   │
│  │  - send() / receive()                                     │   │
│  │  - handle() - APDU routing                               │   │
│  │  - State management (associating, associated)            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                      Security Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Security Suite 0/1/2                                     │   │
│  │  encrypt() / decrypt() / gmac()                           │   │
│  │  HLS authentication (GMAC, Common)                         │   │
│  │  Key management                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                   Protocol Layer (XDLMS/APDU)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ GET Request  │  │  SET Request  │  │ ACTION Req.  │       │
│  │ GET Response │  │  SET Response │  │ ACTION Resp. │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Block Transfer (General Block Transfer)               │   │
│  │  With List operations (GET/SET/ACTION)                  │   │
│  │  Selective Access (RangeDescriptor, EntryDescriptor)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                   HDLC Transport Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ SNRM Frame   │  │   UA Frame    │  │   I-Frame    │       │
│  │   RR Frame   │  │  Disconnect   │  │  Information │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Parameter Negotiation (window size, max frame length)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│                      I/O Layer                                 │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │  TCP/UDP     │  │  Serial Port  │                           │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## Module Organization

```
dlms_cosem/
├── __init__.py              # Package exports
├── client.py                # DlmsClient - main user interface
├── connection.py            # DlmsConnection - connection management
├── exceptions.py            # Exception hierarchy
├── security.py              # Cryptography and authentication
├── io.py                    # Transport interfaces
├── a_xdr.py                 # AXDR encoding/decoding
├── dlms_data.py             # DLMS data types
├── enumerations.py          # DLMS enumerations
├── utils.py                 # Utility functions
│
├── cosem/                   # COSEM interface objects
│   ├── __init__.py
│   ├── obis.py               # OBIS code handling
│   ├── interface_classes.py
│   ├── attributes.py
│   ├── selective_access.py  # RangeDescriptor, EntryDescriptor
│   └── capture_object.py
│
├── protocol/                # DLMS protocol
│   ├── acse/                # Application Connection
│   │   ├── association.py
│   │   └── base.py
│   └── xdlms/               # XDLMS APDUs
│       ├── get.py
│       ├── set.py
│       ├── action.py
│       ├── general_block_transfer.py
│       └── confirmed_service_error.py
│
├── hdlc/                    # HDLC transport
│   ├── __init__.py
│   ├── frames.py            # HDLC frames (SNRM, UA, I-Frame, etc.)
│   ├── parameters.py        # Parameter negotiation
│   ├── address.py           # HDLC addresses
│   └── fields.py            # HDLC control fields
│
├── key_management/         # Security key management
│   ├── security_suite.py
│   ├── key_generator.py
│   ├── key_manager.py
│   ├── key_storage.py
│   ├── key_rotator.py
│   └── formatters.py
│
├── parsers.py               # Data parsers (ProfileGenericBufferParser)
├── time.py                  # DLMS time handling
└── state.py                 # Connection state management
```

## Key Components

### DlmsClient

The main interface for communicating with DLMS/COSEM devices.

```python
from dlms_cosem import DlmsClient
from dlms_cosem.io import TcpTransport
from dlms_cosem.security import HighLevelSecurityGmacAuthentication

# Create client
transport = TcpTransport(host="192.168.1.100", port=4059)
auth = HighLevelSecurityGmacAuthentication(challenge_length=32)

client = DlmsClient(transport, auth=auth)

# Associate with meter
client.associate()

# Read data
attribute = CosemAttribute(interface=..., instance=..., attribute=...)
data = client.get(attribute)

# Disconnect
client.disconnect()
```

### Exception Hierarchy

```
DlmsException (base)
├── DlmsProtocolError (1000-1999)
├── DlmsSecurityError (2000-2999)
├── DlmsConnectionError (3000-3999)
├── DlmsClientError (4000-4999)
└── DlmsDataError (5000-5999)
```

### HDLC Parameter Negotiation

HDLC parameters can be negotiated during connection establishment to improve performance:

```python
from dlms_cosem.hdlc import HdlcParameterList, negotiate_parameters

# Client proposes parameters
client_params = HdlcParameterList()
client_params.set_window_size(5)
client_params.set_max_info_length_tx(1024)

# Server responds with its capabilities
server_params = HdlcParameterList()
server_params.set_window_size(3)

# Negotiate (uses minimum values)
negotiated = negotiate_parameters(client_params, server_params)
```

### Profile Generic Access

Multiple ways to access Profile Generic (load profile) data:

1. **ReadByRange** - Filter by time range
2. **ReadByEntry** - Filter by entry index
3. **Column Filtering** - Parse only specific columns

```python
# Read data for January 2024
data = client.get_with_range(
    profile_attr,
    from_value=datetime(2024, 1, 1),
    to_value=datetime(2024, 1, 31)
)

# Read first 100 entries, columns 1-5 only
data = client.get_with_entry(
    profile_attr,
    from_entry=1,
    to_entry=100,
    from_selected_value=1,
    to_selected_value=5
)
```

## Design Patterns

### Factory Pattern

Used for creating APDU objects:

```python
class GetRequestFactory:
    @staticmethod
    def from_bytes(data: bytes) -> GetRequest:
        # Parse and create appropriate GetRequest subclass
        ...
```

### Strategy Pattern

Used for authentication methods:

```python
class AuthenticationMethodManager(Protocol):
    def get_calling_authentication_value(self) -> bytes: ...
    def hls_generate_reply_data(self, connection) -> bytes: ...

# Implementations:
# - NoSecurityAuthentication
# - LowLevelSecurityAuthentication
# - HighLevelSecurityGmacAuthentication
# - HighLevelSecurityCommonAuthentication
```

### Builder Pattern

Used for complex configuration:

```python
KeyManager.generate(
    suite=0,
    name="production",
    system_title=b"MDMID000"
)
```

## Security Architecture

### Security Suites

| Suite | Algorithm | Key Length | Use Case |
|-------|-----------|------------|----------|
| 0 | AES-128-GCM | 16 bytes | Standard security |
| 1 | AES-128-GCM | 16 bytes | Same as Suite 0 |
| 2 | AES-256-GCM | 32 bytes | High security (future) |

### Authentication Flow

```
Client                  Meter
  │                        │
  ├──── AARQ ──────────────►│
  │◄─── AARE ───────────────┤
  │                        │
  ├──── HLS Request ──────►│
  │◄─── HLS Response ───────┤
  │                        │
  ├──── Global Cipher ─────►│
  │◄─── Global Cipher ──────┤
  │                        │
  ├──── Action Request ────►│
  │◄─── Action Response ────┤
```

## Data Flow

### GET Request Flow

```
Client                          Meter
  │                              │
  ├─ GetRequestNormal ─────────►│
  │   (with RangeDescriptor)    │
  │                              │
  ├─────────────────────────────┤
  │◄─ GetResponseNormal ────────│
  │   (with profile data)        │
  │                              │
  ├─ [Block Transfer] ─────────►│
  │◄─ [GetResponseWithBlock] ────│
  │                              │
  ├─ GetRequestNext ────────────►│
  │◄─ GetResponseLastBlock ──────│
  │                              │
```

### Error Handling Flow

```
Application
    │
    ├─ try: client.get()
    │
    ├─ except DlmsTimeoutError
    │  └─ Action: Retry with backoff
    │
    ├─ except DlmsSecurityError
    │  └─ Action: Check credentials
    │
    ├─ except DlmsProtocolError
    │  └─ Action: Check conformance
    │
    └─ except DlmsException
       └─ Action: Log and investigate
```

## Performance Considerations

### Throughput Optimization

1. **HDLC Window Size** - More frames per acknowledgment
   - Default: 1
   - Optimized: 3-7

2. **Max Info Length** - More data per frame
   - Default: 128 bytes
   - Optimized: 512-2048 bytes

3. **Block Transfer** - Efficient large data handling
   - Automatic for data > 128 bytes

4. **Column Filtering** - Reduce data transfer and parsing
   - Only get columns you need

### Memory Efficiency

1. **Streaming Parsing** - Don't load all data into memory
2. **Selective Access** - Filter at source
3. **Entry Range** - Only parse needed entries
