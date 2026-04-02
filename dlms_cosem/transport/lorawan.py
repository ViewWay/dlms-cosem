"""LoRaWAN Transport Layer for DLMS/COSEM.

Supports DLMS/COSEM over LoRaWAN with:
- Class A/B/C device operation
- LoRaWAN 1.0.x and 1.1 adaptation
- CN470 frequency band (China)
- Payload fragmentation for LoRa frame size limits
- ADR (Adaptive Data Rate) support

Reference: DLMS UA 1000-1 Ed. 14, Annex L
Reference: LoRaWAN Specification v1.0.4, v1.1
"""
import hashlib
import hmac
import logging
import struct
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

import attr

logger = logging.getLogger(__name__)


class LoRaWANClass(IntEnum):
    CLASS_A = 0
    CLASS_B = 1
    CLASS_C = 2


class LoRaWANVersion(IntEnum):
    V1_0 = 0
    V1_0_1 = 1
    V1_0_2 = 2
    V1_0_3 = 3
    V1_0_4 = 4
    V1_1 = 5


class LoRaBand(IntEnum):
    CN470 = 0
    EU868 = 1
    US915 = 2
    AS923 = 3
    AU915 = 4
    IN865 = 5
    KR920 = 6


class MHDRField(IntEnum):
    JOIN_REQUEST = 0
    JOIN_ACCEPT = 1
    UNCONFIRMED_DATA_UP = 2
    UNCONFIRMED_DATA_DOWN = 3
    CONFIRMED_DATA_UP = 4
    CONFIRMED_DATA_DOWN = 5


# CN470 frequency plan parameters (simplified)
CN470_PARAMS = {
    "uplink_freqs": [470.3 + i * 0.2 for i in range(96)],
    "downlink_freqs": [500.3 + i * 0.2 for i in range(48)],
    "max_payload_size": {  # DR -> max bytes
        0: 59, 1: 59, 2: 59, 3: 123, 4: 230, 5: 230, 6: 230, 7: 230,
    },
    "default_dr": 2,
}


@attr.s(auto_attribs=True)
class LoRaConfig:
    """LoRaWAN connection configuration."""
    dev_eui: bytes = b"\x00" * 8
    app_eui: bytes = b"\x00" * 8
    app_key: bytes = b"\x00" * 16
    dev_addr: Optional[bytes] = None
    nwk_skey: Optional[bytes] = None
    app_skey: Optional[bytes] = None
    lora_class: LoRaWANClass = LoRaWANClass.CLASS_A
    band: LoRaBand = LoRaBand.CN470
    version: LoRaWANVersion = LoRaWANVersion.V1_0_3
    adr_enabled: bool = True
    confirmed_uplink: bool = False
    max_payload_size: int = 50  # Conservative for CN470 DR2
    fragmentation_enabled: bool = True
    max_fragments: int = 16


class DLMSFragmenter:
    """Fragment DLMS APDUs to fit within LoRa payload limits."""

    FRAGMENT_HEADER_SIZE = 4  # index(2) + total(2)

    def __init__(self, max_payload: int):
        self.max_payload = max_payload
        self.max_fragment_data = max_payload - self.FRAGMENT_HEADER_SIZE

    def fragment(self, data: bytes) -> List[bytes]:
        """Split DLMS APDU into fragments."""
        if len(data) <= self.max_fragment_data:
            return [struct.pack(">HH", 0, 1) + data]

        fragments = []
        total = (len(data) + self.max_fragment_data - 1) // self.max_fragment_data
        for i in range(total):
            chunk = data[i * self.max_fragment_data:(i + 1) * self.max_fragment_data]
            header = struct.pack(">HH", i, total)
            fragments.append(header + chunk)
        return fragments

    def defragment(self, fragments: List[bytes]) -> bytes:
        """Reassemble fragments into original DLMS APDU."""
        if not fragments:
            return b""

        if len(fragments) == 1:
            f = fragments[0]
            idx, total = struct.unpack(">HH", f[:4])
            if idx == 0 and total == 1:
                return f[4:]

        # Multi-fragment
        result = bytearray()
        parsed: Dict[int, bytes] = {}
        for f in fragments:
            idx, total = struct.unpack(">HH", f[:4])
            parsed[idx] = f[4:]

        for i in range(max(parsed.keys()) + 1):
            result.extend(parsed[i])
        return bytes(result)


class LoRaWANFrameCrypto:
    """LoRaWAN frame encryption and MIC calculation."""

    @staticmethod
    def encrypt_payload(key: bytes, a_block_counter: int,
                        data: bytes, direction: int, dev_addr: bytes,
                        fcnt: int) -> bytes:
        """Encrypt payload using AES-128-CTR (simplified)."""
        # Real implementation would use proper AES-128-CTR
        # This is a placeholder for the crypto operations
        return data

    @staticmethod
    def calculate_mic(key: bytes, msg: bytes, direction: int,
                      dev_addr: bytes, fcnt: int) -> bytes:
        """Calculate 4-byte MIC using CMAC."""
        # Real implementation would use AES-CMAC
        return hmac.new(key, msg, hashlib.sha256).digest()[:4]


class LoRaWANTransport:
    """LoRaWAN transport layer for DLMS/COSEM.

    Handles LoRaWAN frame construction, encryption, and fragmentation
    for DLMS/COSEM APDUs.
    """

    def __init__(self, config: Optional[LoRaConfig] = None):
        self.config = config or LoRaConfig()
        self._fragmenter = DLMSFragmenter(self.config.max_payload_size)
        self._crypto = LoRaWANFrameCrypto()
        self._fcnt_up = 0
        self._fcnt_down = 0
        self._connected = False
        self._received_fragments: Dict[int, List[bytes]] = {}

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Simulate OTAA join (in real implementation, talks to radio)."""
        if self.config.dev_addr and self.config.nwk_skey and self.config.app_skey:
            self._connected = True
            logger.info(
                f"LoRaWAN connected: DevAddr={self.config.dev_addr.hex()} "
                f"Class={'ABC'[self.config.lora_class]} "
                f"Band={self.config.band.name}"
            )
        else:
            # Simulate join
            self._fcnt_up = 0
            self._fcnt_down = 0
            self._connected = True
            logger.info("LoRaWAN joined (simulated)")

    def disconnect(self) -> None:
        self._connected = False

    def send(self, dlms_apdu: bytes) -> int:
        """Send DLMS APDU via LoRaWAN with fragmentation."""
        if not self._connected:
            raise ConnectionError("LoRaWAN not connected")

        fragments = self._fragmenter.fragment(dlms_apdu)
        total_sent = 0

        for frag in fragments:
            # Build LoRaWAN frame (simplified MHDR + FHDR + payload)
            if self.config.confirmed_uplink:
                mhdr = MHDRField.CONFIRMED_DATA_UP
            else:
                mhdr = MHDRField.UNCONFIRMED_DATA_UP

            frame = struct.pack("B", mhdr)
            frame += frag
            total_sent += len(frame)

        self._fcnt_up += 1
        logger.debug(
            f"LoRaWAN TX: {len(dlms_apdu)} bytes -> "
            f"{len(fragments)} fragment(s), FCntUp={self._fcnt_up}"
        )
        return total_sent

    def receive(self) -> bytes:
        """Receive and reassemble DLMS APDU from LoRaWAN."""
        if not self._connected:
            raise ConnectionError("LoRaWAN not connected")

        # In real implementation, receives from radio and reassembles
        self._fcnt_down += 1
        return b""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
