"""SML (Smart Message Language) parser for German/European meters."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Any, Tuple

import structlog

LOG = structlog.get_logger()


class SMLTag(IntEnum):
    """SML TLV tags."""
    END_OF_SML_FILE = 0x1b
    GET_OPEN_REQUEST = 0x01
    GET_OPEN_RESPONSE = 0x02
    GET_CLOSE_REQUEST = 0x03
    GET_CLOSE_RESPONSE = 0x04
    GET_PROFILE_LIST_REQUEST = 0x05
    GET_PROFILE_LIST_RESPONSE = 0x06
    GET_PROC_PARAMETER_REQUEST = 0x07
    GET_PROC_PARAMETER_RESPONSE = 0x08
    SET_PROC_PARAMETER_REQUEST = 0x09
    ATTENTION_RESPONSE = 0x10

    # Sub-tags
    PUBLIC_KEY = 0x01
    PUBLIC_KEY_SIGNATURE = 0x02
    SERVER_ID = 0x01
    CLIENT_ID = 0x02
    VALUE_LIST = 0x76
    ENTRY = 0x77
    SCALER_UNIT = 0x52
    VALUE = 0x63


class SMLType(IntEnum):
    """SML value types."""
    OCTET_STRING = 0x01
    INTEGER_8 = 0x02
    INTEGER_16 = 0x03
    INTEGER_32 = 0x05
    INTEGER_64 = 0x09
    UNSIGNED_8 = 0x10
    UNSIGNED_16 = 0x11
    UNSIGNED_32 = 0x13
    UNSIGNED_64 = 0x17
    BOOLEAN = 0x21
    BITSTRING = 0x22
    BCD = 0x41
    LIST = 0x70  # variable length
    LIST_WITH_LENGTH = 0x71  # 1 byte length
    LIST_WITH_LENGTH2 = 0x72  # 2 byte length
    OPTIONAL = 0x01  # within lists
    SEQUENCE = 0x77


class SMLSignatureMode(IntEnum):
    """SML cryptographic signature modes."""
    NONE = 0
    AES_CMAC = 1
    RSA_SHA256 = 2
    ECDSA_P256 = 3


@dataclass
class SMLPublicKey:
    """SML public key information."""
    key_type: int = 0
    key_value: bytes = b""
    key_exp: int = 65537
    signature_mode: SMLSignatureMode = SMLSignatureMode.NONE

    @property
    def fingerprint(self) -> str:
        import hashlib
        return hashlib.sha256(self.key_value).hexdigest()

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify data signature."""
        if self.signature_mode == SMLSignatureMode.NONE:
            return True
        # Placeholder - real implementation needs cryptography lib
        LOG.warning("sml_verify_not_implemented", mode=self.signature_mode.name)
        return False


@dataclass
class SMLValueEntry:
    """A single SML value entry from a value list."""
    obis: bytes
    value: Any
    unit: Optional[int] = None
    scaler: Optional[int] = None
    status: Optional[int] = None
    timestamp: Optional[int] = None

    @property
    def obis_str(self) -> str:
        parts = list(self.obis)
        return f"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]}.{parts[4]}.{parts[5]}"


@dataclass
class SMLMessage:
    """Parsed SML message."""
    tag: SMLTag
    transaction_id: bytes = b""
    group_no: int = 0
    abort_on_error: int = 0
    body: Optional[Any] = None
    crc: Optional[int] = None


@dataclass
class SMLFile:
    """Complete SML file with messages."""
    messages: List[SMLMessage] = field(default_factory=list)
    public_key: Optional[SMLPublicKey] = None

    def get_value_entries(self) -> List[SMLValueEntry]:
        """Extract all value entries from profile list responses."""
        entries = []
        for msg in self.messages:
            if msg.tag == SMLTag.GET_PROFILE_LIST_RESPONSE:
                entries.extend(self._extract_entries(msg.body))
        return entries

    @staticmethod
    def _extract_entries(body: Any) -> List[SMLValueEntry]:
        """Extract value entries from response body."""
        entries = []
        if isinstance(body, list) and len(body) > 1:
            value_list = body[1]
            if isinstance(value_list, list):
                for entry in value_list:
                    if isinstance(entry, list) and len(entry) >= 2:
                        obis = entry[0] if isinstance(entry[0], bytes) else b"\x00" * 6
                        value = entry[1] if len(entry) > 1 else None
                        scaler = entry[2] if len(entry) > 2 else None
                        unit = entry[3] if len(entry) > 3 else None
                        entries.append(SMLValueEntry(
                            obis=obis,
                            value=value,
                            scaler=scaler,
                            unit=unit,
                        ))
        return entries


class SMLParser:
    """Parser for SML (Smart Message Language) protocol.

    SML is used by German/European energy meters as defined in
    BSI TR-03109 and EDL 21.
    """

    ESCAPE_BYTE = 0x1b
    LIST_BASE = 0x70

    def __init__(self, check_crc: bool = False):
        self.check_crc = check_crc
        self._pos = 0
        self._data = b""

    def parse(self, data: bytes) -> SMLFile:
        """Parse complete SML file."""
        self._data = data
        self._pos = 0
        sml_file = SMLFile()

        while self._pos < len(self._data):
            if self._data[self._pos] == self.ESCAPE_BYTE:
                # Check for end of file
                if self._pos + 3 <= len(self._data) and self._data[self._pos + 1:self._pos + 4] == b"\x1b\x1b\x1b":
                    break

            tag = self._read_u8()
            sml_tag = SMLTag(tag) if tag in [t.value for t in SMLTag] else None

            if sml_tag == SMLTag.END_OF_SML_FILE:
                break

            try:
                msg = self._parse_message(tag, sml_tag)
                if msg:
                    sml_file.messages.append(msg)
            except Exception as e:
                LOG.warning("sml_parse_error", pos=self._pos, error=e)
                break

        return sml_file

    def _read_u8(self) -> int:
        val = self._data[self._pos]
        self._pos += 1
        return val

    def _read_bytes(self, length: int) -> bytes:
        val = self._data[self._pos:self._pos + length]
        self._pos += length
        return val

    def _parse_tlv(self) -> Tuple[int, Any]:
        """Parse a TLV element."""
        tag = self._read_u8()

        if tag in (0x01, 0x10, 0x21):  # 1-byte values
            return tag, self._read_u8()
        elif tag in (0x02, 0x11):  # 2-byte values
            return tag, struct.unpack(">h", self._read_bytes(2))[0]
        elif tag in (0x05, 0x13):  # 4-byte values
            return tag, struct.unpack(">i", self._read_bytes(4))[0]
        elif tag in (0x09, 0x17):  # 8-byte values
            return tag, struct.unpack(">q", self._read_bytes(8))[0]
        elif tag == 0x06:  # unsigned 16
            return tag, struct.unpack(">H", self._read_bytes(2))[0]
        elif tag == 0x14:  # unsigned 32
            return tag, struct.unpack(">I", self._read_bytes(4))[0]
        elif tag == 0x15:  # unsigned 64
            return tag, struct.unpack(">Q", self._read_bytes(8))[0]
        elif tag == 0x16:  # integer 8
            return tag, self._read_u8()
        else:
            # Try to parse as list or octet string
            return tag, self._read_u8()

    def _parse_message(self, tag: int, sml_tag: Optional[SMLTag]) -> Optional[SMLMessage]:
        """Parse an SML message."""
        if sml_tag is None:
            # Unknown tag, try to skip
            return None

        msg = SMLMessage(tag=sml_tag)

        # Read transaction ID (4 bytes)
        if self._pos + 4 <= len(self._data):
            msg.transaction_id = self._read_bytes(4)

        # Read group_no (2 bytes)
        if self._pos + 2 <= len(self._data):
            msg.group_no = struct.unpack(">H", self._read_bytes(2))[0]

        # Read abort_on_error (1 byte)
        if self._pos + 1 <= len(self._data):
            msg.abort_on_error = self._read_u8()

        # Parse body based on tag
        msg.body = self._parse_body(sml_tag)

        # Read CRC (2 bytes)
        if self._pos + 2 <= len(self._data):
            msg.crc = struct.unpack(">H", self._read_bytes(2))[0]

        return msg

    def _parse_body(self, tag: SMLTag) -> Any:
        """Parse message body based on tag type."""
        if tag in (
            SMLTag.GET_OPEN_RESPONSE,
            SMLTag.GET_PROFILE_LIST_RESPONSE,
            SMLTag.GET_PROC_PARAMETER_RESPONSE,
        ):
            return self._parse_list()
        elif tag == SMLTag.GET_CLOSE_RESPONSE:
            # Signature
            return self._read_bytes(8) if self._pos + 8 <= len(self._data) else None
        return None

    def _parse_list(self) -> List:
        """Parse an SML list."""
        tag = self._read_u8()
        if not (0x70 <= tag <= 0x7f):
            self._pos -= 1
            return []

        length = tag & 0x0f
        if length == 15:
            length = self._read_u8() + 15

        result = []
        for _ in range(length):
            result.append(self._parse_element())
        return result

    def _parse_element(self) -> Any:
        """Parse a single SML element."""
        if self._pos >= len(self._data):
            return None

        tag = self._data[self._pos]
        self._pos += 1

        if tag == 0x00:
            return None
        elif tag == 0x01:
            return self._read_u8()
        elif tag == 0x02:
            return struct.unpack(">h", self._read_bytes(2))[0]
        elif tag in (0x03, 0x06):
            return struct.unpack(">H", self._read_bytes(2))[0]
        elif tag == 0x04:
            return struct.unpack(">i", self._read_bytes(4))[0]
        elif tag in (0x05, 0x0f):
            return struct.unpack(">I", self._read_bytes(4))[0]
        elif tag == 0x09:
            return struct.unpack(">q", self._read_bytes(8))[0]
        elif tag == 0x10:
            return self._read_u8()
        elif tag == 0x11:
            return struct.unpack(">h", self._read_bytes(2))[0]
        elif tag in (0x12, 0x16):
            return self._read_u8()
        elif tag in (0x13, 0x15):
            return struct.unpack(">I", self._read_bytes(4))[0]
        elif tag == 0x14:
            return struct.unpack(">I", self._read_bytes(4))[0]
        elif tag == 0x17:
            return struct.unpack(">Q", self._read_bytes(8))[0]
        elif tag == 0x21:
            return bool(self._read_u8())
        elif tag == 0x41:
            return self._read_bytes(8)  # BCD
        elif 0x70 <= tag <= 0x7f:
            length = tag & 0x0f
            if length == 15:
                length = self._read_u8() + 15
            return [self._parse_element() for _ in range(length)]
        elif tag == 0x01:
            # Octet string
            length = self._read_u8()
            return self._read_bytes(length)
        else:
            # Assume octet string with length
            length = self._read_u8() if self._pos < len(self._data) else 0
            if length > 0 and self._pos + length <= len(self._data):
                return self._read_bytes(length)
            return None


class SMLToDLMSBridge:
    """Bridge between SML and DLMS/COSEM data models.

    Converts SML value entries to COSEM OBIS format for interoperability.
    """

    # Common SML OBIS codes mapped to COSEM names
    OBIS_MAP = {
        "1.0.1.8.0.255": "Active Power +",
        "1.0.2.8.0.255": "Active Power -",
        "1.0.31.7.0.255": "Voltage L1",
        "1.0.51.7.0.255": "Current L1",
        "1.0.1.7.0.255": "Active Power Total +",
        "0.0.96.1.0.255": "Server ID",
        "0.0.0.9.0.255": "Meter Firmware Version",
        "1.0.0.0.0.255": "Meter Address",
    }

    @classmethod
    def sml_entry_to_cosem(cls, entry: SMLValueEntry) -> dict:
        """Convert SML entry to COSEM-compatible dict."""
        return {
            "obis": entry.obis_str,
            "value": entry.value,
            "unit": entry.unit,
            "scaler": entry.scaler,
            "cosem_name": cls.OBIS_MAP.get(entry.obis_str, "Unknown"),
        }

    @classmethod
    def obis_bytes_to_str(cls, obis: bytes) -> str:
        """Convert OBIS bytes to string."""
        if len(obis) >= 6:
            return f"{obis[0]}.{obis[1]}.{obis[2]}.{obis[3]}.{obis[4]}.{obis[5]}"
        return ".".join(str(b) for b in obis)

    @classmethod
    def parse_meter_data(cls, data: bytes) -> List[dict]:
        """Parse SML data and return COSEM-compatible entries."""
        parser = SMLParser()
        sml_file = parser.parse(data)
        entries = sml_file.get_value_entries()
        return [cls.sml_entry_to_cosem(e) for e in entries]
