# dlms-cosem

**Complete DLMS/COSEM protocol stack for Python** — sans-io implementation with HDLC framing, A-XDR codec, 50+ COSEM IC classes, multiple transport layers, security suites, server, automation, and analytics.

[![Tests](https://img.shields.io/badge/tests-5146%20passed-brightgreen)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![License: BSL 1.1](https://img.shields.io/badge/license-BSL%201.1-orange.svg)]()

## Features

### Full DLMS/COSEM Protocol Stack
- **COSEM Application Layer**: GET, SET, ACTION, GET.WITH_LIST, Data Notification
- **ACSE Association**: AARQ/AARE with HLS-ISM and LLS authentication
- **A-XDR Codec**: Complete ASN.1-based DLMS data encoding/decoding
- **HDLC Framing**: Full LLC/MAC layer with segmentation, windowing, and CRC-16

### COSEM IC Classes (50+)

| Class | IC | Description |
|-------|----|-------------|
| Register | 3 | Generic register |
| Demand Register | 5 | Demand measuring |
| Register Activation | 6 | Register activation control |
| Register Table | 4 | Tabular register data |
| Extended Register | 18 | Extended with status flags |
| Register Monitor | 36 | Register monitoring |
| Clock | 8 | Date/time management |
| Script Table | 9 | Action scheduling |
| Special Day Table | 11 | Holiday/special day config |
| Season Profile | 14 | Season time switching |
| Week Profile | 15 | Weekly schedule |
| Day Profile | 16 | Daily schedule |
| Activity Calendar | 20 | Tariff schedule |
| Load Profile | 7 | Interval data recording |
| Profile Generic | 1 | Generic profile data |
| Data | 1 | Generic data container |
| Value With Register | 13 | Data with register reference |
| Attribute With Selection | 34 | Selection-based attribute |
| Capture Object | 21 | Profile capture definitions |
| Event Log | 7 | Event recording (PG-based) |
| Standard Event Log | 27 | Standardized event log |
| Utility Event Log | 28 | Utility-specific events |
| Auto Answer | 28 | Automatic answering |
| Modem Configuration | 105 | Modem parameters |
| Modem Setup | 27 | Modem initialization |
| GPRS Setup | 45 | GPRS connectivity |
| TCP/UDP Setup | 41 | IP connectivity |
| NB-IoT Setup | — | NB-IoT parameters |
| LoRa Setup | — | LoRaWAN parameters |
| ZigBee Setup | 110 | ZigBee network |
| RS485 Setup | — | Serial communication |
| Infrared Setup | 24 | Optical port config |
| Local Port Setup | 19 | Port configuration |
| Security Setup | — | DLMS security |
| Image Transfer | — | Firmware update |
| Energy Register | — | Energy measurement |
| Power Register | — | Power measurement |
| Voltage | — | Voltage monitoring |
| Current | — | Current monitoring |
| Frequency | — | Frequency monitoring |
| Power Factor | — | Power quality |
| Max Demand Register | — | Maximum demand |
| Quality Control | 31 | Data quality validation |
| Tariff Plan | — | Tariff configuration |
| Tariff Table | — | Tariff definitions |
| Event Notification | 29 | Push event notification |
| Interrogation Interface | — | Data interrogation |
| Single Action Schedule | — | Single event scheduling |
| Action Schedule | — | Recurring action scheduling |
| Demand Register | 5 | Demand measurement |
| Load Profile Switch | 23 | Load profile control |
| Factory | — | Factory configuration |

### Transport Layers

```
┌─────────────────────────────────────────────┐
│              Application Layer               │
│         (DLMS/COSEM Services)               │
├─────────────────────────────────────────────┤
│              Transport Layer                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌──────┐ ┌─────┐ │
│  │HDLC │ │ TCP │ │ UDP │ │ TLS  │ │ WS  │ │
│  └──┬──┘ └──┬──┘ └──┬──┘ └──┬───┘ └──┬──┘ │
├─────┼───────┼───────┼───────┼────────┼─────┤
│     │  Serial│  IPv4 │  TLS  │  HTTP  │     │
│     │  Port  │  Socket│ Socket│ Upgrade│     │
├─────┴───────┴───────┴───────┴────────┴─────┤
│              IoT Transports                   │
│  ┌─────────┐ ┌──────────┐                   │
│  │ NB-IoT  │ │ LoRaWAN  │                   │
│  └─────────┘ └──────────┘                   │
└─────────────────────────────────────────────┘
```

| Transport | Protocol | Use Case |
|-----------|----------|----------|
| HDLC | Serial (RS-485/Optical) | Wired meter reading |
| TCP | IPv4/IPv6 | IP-based metering |
| UDP | IPv4 | Push data notification |
| TLS | TCP + TLS 1.2+ | Encrypted IP metering |
| WebSocket | HTTP Upgrade | Browser/cloud integration |
| NB-IoT | CoAP/LwM2M | Low-power cellular |
| LoRaWAN | LoRa | Ultra-low-power LPWAN |

### Security Suites

| Suite | Algorithm | Standard |
|-------|-----------|----------|
| HLS-ISM | AES-128-GCM | IEC 62056-53 |
| SM4-GMAC | SM4 (GMAC) | GB/T 32907 |
| SM4-GCM | SM4 (GCM) | GB/T 32907 |
| AES-GCM | AES-128/256-GCM | NIST SP 800-38D |

### Standards Compliance

- **IEC 62056-53** (Green Book) — DLMS/COSEM Application Layer
- **IEC 62056-46** (Blue Book) — HDLC-based Data Link Layer
- **IEC 62056-47** (Yellow Book) — COSEM Transport Layer for IPv4
- **IEC 62056-62** (White Book) — COSEM Interface Classes
- **GB/T 17215.6** — China National Standard for DLMS
- **GB/T 32907** — SM4 Cryptographic Algorithm
- **SML** — Smart Message Language (EDIS)

## Installation

```bash
pip install dlms-cosem
```

With optional dependencies:

```bash
pip install dlms-cosem[test]      # Testing
pip install dlms-cosem[docs]      # Documentation
pip install dlms-cosem[keyring]   # System keyring support
```

## Quick Start

### Client — Read a Register

```python
from dlms_cosem import DlmsClient, DlmsConnectionSettings
from dlms_cosem.io import SerialIO
from dlms_cosem.transport import HdlcTransport

# Serial connection to optical port
io = SerialIO(port="/dev/ttyUSB0", baudrate=2400)
transport = HdlcTransport(io)

settings = DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
    authentication="low",
    password=b"12345678",
)

client = DlmsClient(transport, settings)
await client.connect()

# Read active power register (OBIS 1.0.1.8.0.255)
value = await client.get("1.0.1.8.0.255")
print(f"Active power: {value}")

# Read load profile
profile = await client.get("1.0.99.1.0.255", access="range", from_=0, to_=10)

await client.close()
```

### TCP Transport

```python
from dlms_cosem import DlmsClient, DlmsConnectionSettings
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport

io = TcpIO(host="192.168.1.100", port=4059)
transport = HdlcTransport(io)
client = DlmsClient(transport, DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
))
await client.connect()
data = await client.get("0.0.96.1.0.255")  # Meter ID
await client.close()
```

### Server — Simulate a Meter

```python
from dlms_cosem.server import DlmsServer
from dlms_cosem.cosem.factory import CosemObjectFactory

# Create meter objects
factory = CosemObjectFactory()
factory.register_register("1.0.1.8.0.255", initial_value=1234.5)  # Active power
factory.register_clock("0.0.1.0.0.255")

server = DlmsServer(factory, port=4059)
await server.start()
```

### Automation — Batch Meter Reading

```python
from dlms_cosem.automation import MeterAutomation
from dlms_cosem import DlmsConnectionSettings

automation = MeterAutomation()
automation.add_meter("meter_1", "192.168.1.101", 4059, settings)
automation.add_meter("meter_2", "192.168.1.102", 4059, settings)

# Read all meters in parallel
results = await automation.collect_all([
    "0.0.96.1.0.255",  # Meter ID
    "1.0.1.8.0.255",  # Active power
    "1.0.1.7.0.255",  # Voltage
])
```

### WebSocket Gateway

```python
from dlms_cosem.ws_gateway import WsGateway

gateway = WsGateway(meters={...})
await gateway.start(host="0.0.0.0", port=8080)
# Connect: ws://localhost:8080/meters/{meter_id}
```

### Key Management

```python
from dlms_cosem.key_management import KeyManager, SecuritySuite

km = KeyManager()
km.set_security_suite(SecuritySuite.HLS_ISM)
km.set_key("encryption", b"0123456789abcdef")
km.rotate_key("encryption", schedule="monthly")
```

### SML Parsing

```python
from dlms_cosem.sml import SmlParser

parser = SmlParser()
messages = parser.parse(data)
for msg in messages:
    print(f"Server ID: {msg.server_id}")
    for entry in msg.values:
        print(f"  {entry.obis}: {entry.value}")
```

### China GB Extensions

```python
from dlms_cosem.china_gb import GB17215Meter

meter = GB17215Meter(port="/dev/ttyUSB0")
await meter.connect()
data = await meter.read_demand()  # GB-specific demand reading
```

## Architecture

```
dlms_cosem/
├── __init__.py              # Public API
├── client.py                # DlmsClient (async)
├── server.py                # DlmsServer
├── automation.py            # Batch meter operations
├── security.py              # Authentication & encryption
├── a_xdr.py                 # A-XDR codec
├── parsers.py               # DLMS data parsing
├── enumerations.py          # DLMS enumerations
├── io.py                    # IO adapters (Serial/TCP/UDP)
├── hdlc/                    # HDLC framing layer
│   ├── frames.py            # I/S/U frame handling
│   ├── connection.py        # HDLC connection state
│   ├── window.py            # Sliding window
│   ├── segmentation.py      # Frame segmentation
│   └── crc.py               # CRC-16
├── transport/               # Transport implementations
│   ├── hdlc.py              # HDLC transport
│   ├── tcp.py               # TCP transport
│   ├── udp.py               # UDP transport
│   ├── tls.py               # TLS transport
│   ├── nbiot.py             # NB-IoT transport
│   └── lorawan.py           # LoRaWAN transport
├── protocol/                # DLMS protocol layer
│   ├── xdlms/               # XDLM-S services
│   │   ├── get.py           # GET/GET.WITH_LIST
│   │   ├── set.py           # SET service
│   │   ├── action.py        # ACTION service
│   │   └── data_notification.py
│   └── acse/                # Association control
│       ├── aarq.py          # Association request
│       └── aare.py          # Association response
├── cosem/                   # COSEM IC classes (50+)
│   ├── factory.py           # Object factory
│   ├── register.py          # IC 3
│   ├── clock.py             # IC 8
│   ├── profile_generic.py   # IC 1
│   ├── demand_register.py   # IC 5
│   └── ...
├── sml/                     # SML parser
├── china_gb/                # China GB/T extensions
├── key_management/          # Key management system
│   ├── key_manager.py
│   ├── key_rotator.py
│   ├── key_storage.py
│   └── security_suite.py
├── ws_gateway.py            # WebSocket gateway
├── cli/                     # CLI tools
│   └── dlms_keys.py         # Key management CLI
└── tests/                   # 5146 tests
```

## Performance

Benchmark on Python 3.13, Apple M2, 5146 tests:

| Metric | Value |
|--------|-------|
| Test suite | 5146 passed, 0 failed |
| A-XDR encode/decode | ~1M ops/sec |
| HDLC frame parse | ~500K frames/sec |
| Profile Generic (1000 entries) | ~2ms decode |
| Association handshake | ~5ms (HLS-ISM) |

## Contributing

1. Fork the repository
2. Install dev dependencies: `pip install -e ".[test]"`
3. Run tests: `python -m pytest tests/ -v`
4. Format code: `ruff format .`
5. Lint: `ruff check .`
6. Submit a pull request

### Development Tips

- The library is **sans-io** — transport and protocol are fully decoupled
- All COSEM IC classes follow the pattern in `dlms_cosem/cosem/base.py`
- Use `CosemObjectFactory` for creating meter object collections
- Tests use pytest fixtures for meter simulation

## License

Business Source License 1.1 — see [LICENSE](LICENSE) for details.

## Acknowledgments

Based on [DLMS/COSEM](https://www.dlms.com/) standards by the DLMS User Association. Originally developed by Henrik Palmlund Wahlgren at Palmlund Wahlgren Innovative Technology AB.
