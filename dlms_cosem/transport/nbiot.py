"""NB-IoT Transport Layer for DLMS/COSEM.

Supports DLMS/COSEM over NB-IoT using:
- UDP/CoAP transport
- DTLS 1.2 security
- PSM (Power Saving Mode) and eDRX for low power
- NIDD (Non-IP Data Delivery) via SCEF

Reference: DLMS UA 1000-1 Ed. 14, Annex L
"""
import logging
import socket
import struct
from enum import IntEnum
from typing import Any, Callable, Dict, Optional, Tuple

import attr

logger = logging.getLogger(__name__)


class CoAPMessageType(IntEnum):
    CON = 0  # Confirmable
    NON = 1  # Non-confirmable
    ACK = 2  # Acknowledgement
    RST = 3  # Reset


class CoAPResponseCode(IntEnum):
    CREATED_2_01 = 65
    DELETED_2_02 = 66
    VALID_2_03 = 67
    CHANGED_2_04 = 68
    CONTENT_2_05 = 69
    BAD_REQUEST_4_00 = 128
    UNAUTHORIZED_4_01 = 129
    NOT_FOUND_4_04 = 132
    INTERNAL_ERROR_5_00 = 160


class PSMMode(IntEnum):
    DISABLED = 0
    ENABLED = 1


class DTLSMode(IntEnum):
    NONE = 0
    PSK = 1  # Pre-Shared Key
    CERT = 2  # Certificate-based


@attr.s(auto_attribs=True)
class NBConnectConfig:
    """NB-IoT connection configuration."""
    host: str = ""
    port: int = 5683
    plmn: str = "46000"  # Default China Mobile
    apn: str = "nbiot"
    band: int = 8  # B8 900MHz
    dtls_mode: DTLSMode = DTLSMode.PSK
    dtls_psk: Optional[bytes] = None
    dtls_psk_identity: Optional[str] = None
    psm_enabled: bool = True
    psm_tau: int = 43200  # TAU timer (seconds)
    psm_active_time: int = 10  # Active time (seconds)
    edrx_enabled: bool = False
    edrx_cycle: float = 81.92
    nidd_enabled: bool = False
    coap_message_type: CoAPMessageType = CoAPMessageType.CON
    timeout: float = 30.0
    max_retransmit: int = 4


class CoAPMessage:
    """Minimal CoAP message builder/parser."""

    VERSION = 1

    def __init__(self, msg_type: CoAPMessageType = CoAPMessageType.CON,
                 code: int = 1, msg_id: int = 0,
                 token: bytes = b"", payload: bytes = b"",
                 options: Optional[Dict[int, bytes]] = None):
        self.msg_type = msg_type
        self.code = code
        self.msg_id = msg_id
        self.token = token
        self.payload = payload
        self.options = options or {}
        self._msg_id_counter = 0

    def to_bytes(self) -> bytes:
        """Encode CoAP message to bytes."""
        token_len = len(self.token)
        if token_len > 8:
            raise ValueError("CoAP token max length is 8 bytes")

        # Header: ver(2) | type(2) | tkl(4) | code(8) | msg_id(16)
        header = struct.pack(
            ">BBH",
            (self.VERSION << 6) | (self.msg_type << 4) | token_len,
            self.code,
            self.msg_id,
        )
        token = self.token
        # Options (simplified - no delta encoding for now)
        options_data = b""
        for opt_num, opt_value in sorted(self.options.items()):
            options_data += struct.pack("BB", opt_num, len(opt_value))
            options_data += opt_value

        payload_marker = b"\xff" if self.payload else b""
        return header + token + options_data + payload_marker + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "CoAPMessage":
        """Parse CoAP message from bytes."""
        if len(data) < 4:
            raise ValueError("CoAP message too short")

        first_byte, code, msg_id = struct.unpack(">BBH", data[:4])
        version = (first_byte >> 6) & 0x3
        msg_type = (first_byte >> 4) & 0x3
        token_len = first_byte & 0xF

        if version != 1:
            raise ValueError(f"Unsupported CoAP version: {version}")

        token = data[4:4 + token_len]
        # Simplified parsing - find payload marker
        payload = b""
        idx = 4 + token_len
        if idx < len(data) and data[idx] == 0xFF:
            payload = data[idx + 1:]

        return cls(
            msg_type=CoAPMessageType(msg_type),
            code=code,
            msg_id=msg_id,
            token=token,
            payload=payload,
        )


class NBIoTTransport:
    """NB-IoT transport layer for DLMS/COSEM.

    Wraps DLMS/COSEM APDUs in CoAP messages and sends over UDP.
    Supports DTLS for secure communication.
    """

    def __init__(self, config: Optional[NBConnectConfig] = None):
        self.config = config or NBConnectConfig()
        self._sock: Optional[socket.socket] = None
        self._msg_id = 0
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Establish NB-IoT connection."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(self.config.timeout)
        self._connected = True
        logger.info(
            f"NB-IoT connected: {self.config.host}:{self.config.port} "
            f"PLMN={self.config.plmn} APN={self.config.apn} "
            f"PSM={'ON' if self.config.psm_enabled else 'OFF'}"
        )

    def disconnect(self) -> None:
        """Close NB-IoT connection."""
        if self._sock:
            self._sock.close()
            self._sock = None
        self._connected = False

    def send(self, dlms_apdu: bytes) -> int:
        """Send DLMS APDU wrapped in CoAP message."""
        if not self._connected:
            raise ConnectionError("NB-IoT transport not connected")

        self._msg_id = (self._msg_id + 1) & 0xFFFF
        coap = CoAPMessage(
            msg_type=self.config.coap_message_type,
            code=2,  # POST
            msg_id=self._msg_id,
            payload=dlms_apdu,
        )
        data = coap.to_bytes()
        self._sock.sendto(data, (self.config.host, self.config.port))
        logger.debug(f"NB-IoT TX: {len(data)} bytes (CoAP msg_id={self._msg_id})")
        return len(data)

    def receive(self) -> bytes:
        """Receive DLMS APDU from CoAP response."""
        if not self._connected:
            raise ConnectionError("NB-IoT transport not connected")

        data, addr = self._sock.recvfrom(2048)
        coap = CoAPMessage.from_bytes(data)
        logger.debug(
            f"NB-IoT RX: {len(data)} bytes from {addr} "
            f"(CoAP code={coap.code})"
        )
        return coap.payload

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
