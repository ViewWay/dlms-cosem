# New Modules Guide

This guide covers the new modules added to the dlms-cosem library for China GB standards, SML protocol, and protocol frames.

## Table of Contents

1. [China GB Module](#china-gb-module)
2. [SML Module](#sml-module)
3. [Protocol Frames](#protocol-frames)
4. [Utility Functions](#utility-functions)

---

## China GB Module

The `dlms_cosem.china_gb` module provides support for China GB/T 17215.301 standard smart meters.

### Features

- **Tariff Management**: 4-rate tariff system (Peak, Shoulder, Flat, Valley)
- **RS485 Configuration**: China standard communication parameters
- **CP 28 Frames**: DLMS/T CP 28 local protocol frame handling
- **OBIS Mapping**: China-specific OBIS code extensions

### Basic Usage

```python
from dlms_cosem.china_gb import GBMeter, GBTariffProfile, GBTariffSchedule

# Create a meter
meter = GBMeter(address="123456789012")

# Setup standard China 4-rate tariff
meter.setup_china_standard_tariff()

# Read current tariff at 9:00 AM in summer
tariff = meter.tariff_profile.get_current_tariff(9, 0, GBTimeSeason.SUMMER)
# Returns: GBTariffType.PEAK

# Write and read registers
meter.write_register("1.0.1.8.0.0", 12345.6)
value = meter.read_register("1.0.1.8.0.0")
```

### Tariff Configuration

```python
from dlms_cosem.china_gb import (
    GBTariffProfile, GBTariffSchedule, GBTariffType, GBTimeSeason
)

# Create custom tariff profile
profile = GBTariffProfile(name="Custom Tariff")

# Add peak hours (8:00-11:00, 18:00-21:00)
profile.add_schedule(GBTariffSchedule(
    tariff_type=GBTariffType.PEAK,
    hour_start=8, minute_start=0,
    hour_end=11, minute_end=0,
    season=GBTimeSeason.SUMMER,
))
```

### CP 28 Frame Handling

```python
from dlms_cosem.china_gb import GBCp28Frame, GBCp28Command

# Create a read data frame
frame = GBCp28Frame(
    address=b"METER01",
    command=GBCp28Command.READ_DATA,
    data=b"\x00\x01\x02",
)

# Encode to bytes
encoded = frame.to_bytes()

# Decode from bytes
decoded = GBCp28Frame.from_bytes(encoded)
```

### OBIS Code Mapping

```python
from dlms_cosem.china_gb import GBTariffMapper

# Get OBIS code description
name = GBTariffMapper.get_obis_name("1.0.1.8.0.0")
# Returns: "Peak Active Energy Import"

# Get OBIS for specific energy register
obis = GBTariffMapper.get_energy_obis(
    direction=1,
    tariff=GBTariffType.PEAK
)
# Returns: "1.0.1.8.0.0"
```

---

## SML Module

The `dlms_cosem.sml` module provides support for SML (Smart Message Language) protocol used in German/European meters.

### Features

- **SML Parsing**: Parse SML messages from meter data
- **OBIS Conversion**: Convert between SML and DLMS/COSEM formats
- **Public Key Handling**: Support for meter public keys

### Basic Usage

```python
from dlms_cosem.sml import SMLParser, SMLFile

# Parse SML data
parser = SMLParser()
sml_file = parser.parse(meter_data_bytes)

# Extract value entries
entries = sml_file.get_value_entries()
for entry in entries:
    print(f"{entry.obis_str}: {entry.value}")
```

### SML to DLMS Bridge

```python
from dlms_cosem.sml import SMLToDLMSBridge

# Parse and convert to COSEM format
entries = SMLToDLMSBridge.parse_meter_data(meter_data_bytes)
for entry in entries:
    print(f"OBIS: {entry['obis']}")
    print(f"Value: {entry['value']}")
    print(f"Description: {entry['cosem_name']}")
```

### Working with SML Values

```python
from dlms_cosem.sml import SMLValueEntry

# Create a value entry
entry = SMLValueEntry(
    obis=b"\x01\x00\x01\x08\x00\xff",
    value=12345,
    scaler=-2,
    unit=27,  # Watt
)

# Get formatted OBIS string
print(entry.obis_str)  # "1.0.1.8.0.255"
```

---

## Protocol Frames

The `dlms_cosem.protocol.frame` modules provide support for different frame formats.

### Gateway Frame

Used for GPRS/3G/4G routing with network addressing.

```python
from dlms_cosem.protocol.frame.gateway import GatewayFrame

# Create gateway frame
gw = GatewayFrame(
    network_id=0x01,
    physical_address="METER123",
    user_info=dlms_pdu_data,
)

# Encode and send
frame_bytes = gw.to_bytes()

# Parse response
response = GatewayResponseFrame.from_bytes(response_bytes)
```

### RF Frame

Used for wireless ISM band communication (e.g., 470MHz in China).

```python
from dlms_cosem.protocol.frame.rf import RFFrame

# Create RF frame for channel scan
frame = RFFrame()
scan_bytes = frame.scan_channel(channel=1)

# Connect to meter
connect_bytes = frame.connect_meter(channel=1)

# Parse received RF frame
received = RFFrame.from_bytes(received_bytes)
print(f"Signal quality: {received.signal_quality}")
print(f"Channel state: {received.channel_state}")
```

### RF Signal Quality

```python
from dlms_cosem.protocol.frame.rf import RFSignalQuality

# Parse signal quality
signal = RFSignalQuality.from_bytes(signal_bytes)
print(f"Uplink RSSI: {signal.uplink_signal_strength}")
print(f"Uplink SNR: {signal.uplink_snr}")
```

---

## Utility Functions

The `dlms_cosem.util` module provides common data conversion utilities.

### Data Conversion

```python
from dlms_cosem.util import DataConversion

# Hex/Decimal conversion
dec = DataConversion.hex_to_dec("FF")
hex_str = DataConversion.dec_to_hex_str(255, length=4)

# OBIS conversion
obis_hex = DataConversion.obis_to_hex("1-0:96.1.0.255")
obis_str = DataConversion.hex_to_obis("010096010100FF")

# ASCII/Hex conversion
hex_str = DataConversion.ascii_to_hex("METER")
ascii_str = DataConversion.hex_to_ascii("4D45544552")

# Bytes/Hex conversion
hex_str = DataConversion.bytes_to_hex_str(b"\x01\x02\xFF")
bytes_data = DataConversion.hex_str_to_bytes("01 02 FF")

# BCD conversion
bcd = DataConversion.dec_to_bcd(1234)
dec = DataConversion.bcd_to_dec(bcd)
```

### Logging

```python
from dlms_cosem.util import info, debug, warn, error

info("Connection established")
debug("Received data: {}".format(data))
warn("Unexpected response")
error("Connection failed")
```

### Singleton Pattern

```python
from dlms_cosem.util import Singleton

class MyManager(metaclass=Singleton):
    def __init__(self):
        self.value = 42

# Same instance every time
manager1 = MyManager()
manager2 = MyManager()
assert manager1 is manager2
```

---

## Testing

All new modules include comprehensive tests:

```bash
# Run China GB tests
pytest tests/test_china_gb.py -v

# Run SML tests
pytest tests/test_sml.py -v

# Run protocol frame tests
pytest tests/test_protocol_frames.py -v

# Run protocol ACSE/XDLM-S tests
pytest tests/test_protocol_acse_xdlms.py -v

# Run utility tests
pytest tests/test_util_modules.py -v
```

---

## Standards Compliance

| Module | Standard |
|--------|----------|
| China GB | GB/T 17215.301, GB/T 32907 |
| SML | BSI TR-03109, EDL 21 |
| Gateway Frame | DLMS Blue Book 8.4.4 |
| RF Frame | GB/T 17215.211-2019 |

---

## Lazy Loading

All new modules use lazy loading via `__getattr__` to reduce initial import time and memory footprint:

```python
# Only imports what you use
from dlms_cosem.china_gb import GBMeter  # Only GBMeter is loaded
from dlms_cosem.sml import SMLParser      # Only SMLParser is loaded
```
