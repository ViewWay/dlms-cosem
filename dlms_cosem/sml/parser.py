"""SML parser for Smart Message Language protocol."""
from __future__ import annotations

import struct
from typing import Any, List, Optional, Tuple

from dlms_cosem.sml.models import SMLFile, SMLMessage
from dlms_cosem.sml.types import SMLTag, SMLType


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
            except Exception:
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
            length = self._read_u8()
            return self._read_bytes(length)
        else:
            length = self._read_u8() if self._pos < len(self._data) else 0
            if length > 0 and self._pos + length <= len(self._data):
                return self._read_bytes(length)
            return None
