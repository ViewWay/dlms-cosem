# Release Notes — dlms-cosem v1.0.0

**Release Date:** 2026-04-03

## Overview

dlms-cosem v1.0.0 is the first major stable release of the complete DLMS/COSEM protocol stack for Python. This release provides a production-ready, sans-io implementation covering the full DLMS/COSEM specification from HDLC framing through COSEM application services.

## What's New

### Complete Protocol Stack
- **A-XDR Codec**: Full ASN.1-based encoding/decoding of all DLMS data types
- **HDLC Framing**: Complete LLC/MAC layer with segmentation, sliding window, and CRC-16
- **COSEM Services**: GET, SET, ACTION, GET.WITH_LIST, Data Notification
- **Association Control**: AARQ/AARE with HLS-ISM and Low-Level Security authentication

### 50+ COSEM Interface Classes
All major IC classes from IEC 62056-62 (White Book):
- **Measurement**: Register, Extended Register, Demand Register, Register Monitor, Max Demand Register
- **Energy**: Energy Register, Power Register, Voltage, Current, Frequency, Power Factor
- **Time**: Clock, Script Table, Activity Calendar, Season/Week/Day Profile, Special Day Table
- **Data**: Profile Generic, Register Table, Data, Capture Object
- **Events**: Event Log, Standard Event Log, Utility Event Log, Event Notification
- **Communication**: Modem Setup, Modem Configuration, GPRS Setup, TCP/UDP Setup, NB-IoT Setup, LoRa Setup, ZigBee Setup, RS485 Setup, Infrared Setup, Local Port Setup
- **Control**: Load Profile Switch, Register Activation, Auto Answer, Image Transfer, Quality Control, Interrogation Interface, Action Schedule, Single Action Schedule, Tariff Plan, Tariff Table
- **Factory**: Factory configuration class

### Transport Layers
- **HDLC**: Serial port (RS-485 / Optical)
- **TCP/UDP**: IPv4 metering
- **TLS**: Encrypted metering (TLS 1.2+)
- **WebSocket**: Cloud/browser integration via HTTP upgrade
- **NB-IoT**: Low-power cellular metering
- **LoRaWAN**: Ultra-low-power LPWAN metering

### Security
- **HLS-ISM**: IEC 62056-53 standard (AES-128-GCM)
- **SM4-GMAC**: Chinese national standard (GB/T 32907)
- **SM4-GCM**: Chinese national standard authenticated encryption
- **AES-GCM-128/256**: NIST SP 800-38D

### Key Management
- Centralized key management with rotation scheduling
- Multiple storage backends (file, keyring)
- Security suite abstraction

### China National Standard Support
- GB/T 17215.6 DLMS extensions
- SM4 cryptographic algorithm
- China-specific meter reading workflows

### SML Parser
- Smart Message Language (EDIS) parsing support
- Server ID, value list, and OBIS extraction

### COSEM Server
- Simulate meters for development and testing
- CosemObjectFactory for rapid meter configuration
- Full XDLM-S service response handling

### Automation Framework
- Parallel batch meter reading
- Configurable collection schedules
- Error handling and retry logic

### WebSocket Gateway
- Real-time meter data streaming
- Browser-accessible meter interface
- Multi-meter support

### Quality
- **5,146 tests** — all passing, 0 failures
- Fuzzing harnesses for protocol robustness
- Property-based testing
- Performance benchmarks

## Migration from 2026.1.0

This is a major release with significant new functionality. Key changes:

1. **New module structure**: `dlms_cosem.cosem.*` for IC classes, `dlms_cosem.protocol.*` for protocol services
2. **Async-first**: Full async/await API (sync wrappers still available)
3. **Transport composition**: Transport and IO are now fully decoupled

The core client API (`DlmsClient`, `DlmsConnectionSettings`) remains backward-compatible.

## Installation

```bash
pip install dlms-cosem
```

## Minimum Requirements

- Python 3.9+
- cryptography >= 35.0.0
- attrs >= 22.2.0
- pyserial >= 3.5

## License

Business Source License 1.1
