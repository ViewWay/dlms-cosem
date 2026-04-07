"""IC class 72 - M-Bus Client.

M-Bus client for reading M-Bus slave devices.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.4.5
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription
import struct


@attr.s(auto_attribs=True)
class MBusClient:
    """COSEM IC M-Bus Client (class_id=72).

    Attributes:
        1: logical_name (static)
        2: mbus_port_reference (dynamic) - Reference to M-Bus port
        3: capture_definition (dynamic) - What data to capture
        4: capture_period (dynamic) - Period between captures
        5: primary_addresses (dynamic) - List of primary addresses
        6: identification_number (dynamic) - M-Bus identification number
        7: manufacturer_id (dynamic) - Manufacturer identifier
        8: version (dynamic) - M-Bus device version
        9: device_type (dynamic) - Type of M-Bus device
        10: access_number (dynamic) - Access counter
        11: status (dynamic) - M-Bus status
        12: alarm (dynamic) - M-Bus alarm status
    Methods:
        1: reset
        2: capture
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_CLIENT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mbus_port_reference: Optional[Obis] = None
    capture_definition: List[Dict[str, Any]] = attr.ib(factory=list)
    capture_period: int = 0
    primary_addresses: List[int] = attr.ib(factory=list)
    identification_number: str = ""
    manufacturer_id: str = ""
    version: int = 0
    device_type: int = 0
    access_number: int = 0
    status: int = 0
    alarm: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="mbus_port_reference"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_definition"),
        4: AttributeDescription(attribute_id=4, attribute_name="capture_period"),
        5: AttributeDescription(attribute_id=5, attribute_name="primary_addresses"),
        6: AttributeDescription(attribute_id=6, attribute_name="identification_number"),
        7: AttributeDescription(attribute_id=7, attribute_name="manufacturer_id"),
        8: AttributeDescription(attribute_id=8, attribute_name="version"),
        9: AttributeDescription(attribute_id=9, attribute_name="device_type"),
        10: AttributeDescription(attribute_id=10, attribute_name="access_number"),
        11: AttributeDescription(attribute_id=11, attribute_name="status"),
        12: AttributeDescription(attribute_id=12, attribute_name="alarm"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "capture",
    }

    def reset(self) -> None:
        """Method 1: Reset M-Bus client to defaults."""
        self.capture_definition = []
        self.capture_period = 0
        self.access_number = 0
        self.status = 0
        self.alarm = 0

    def capture(self) -> None:
        """Method 2: Trigger immediate data capture."""
        self.access_number += 1

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES


    @staticmethod
    def _encode_tlv(tag: int, data: bytes) -> bytes:
        """Encode a DLMS TLV element."""
        length = len(data)
        if length < 128:
            return bytes([tag, length]) + data
        elif length < 256:
            return bytes([tag, 0x81, length]) + data
        else:
            return bytes([tag, 0x82, (length >> 8) & 0xFF, length & 0xFF]) + data

    @staticmethod
    def _decode_tlv(data: bytes, offset: int = 0):
        """Decode a DLMS TLV element. Returns (tag, value, next_offset)."""
        if offset >= len(data):
            raise ValueError("Unexpected end of data in TLV decode")
        tag = data[offset]
        length = data[offset + 1]
        off = offset + 2
        if length & 0x80:
            num_len = length & 0x7F
            length = int.from_bytes(data[off:off + num_len], 'big')
            off += num_len
        value = data[off:off + length]
        return tag, value, off + length

    def _encode_octet_string(self, data: bytes) -> bytes:
        """Encode octet-string (tag 0x09)."""
        return self._encode_tlv(0x09, data)

    def _encode_boolean(self, value: bool | None) -> bytes:
        if value is None: return bytes([0x00])
        """Encode boolean (tag 0x03)."""
        return self._encode_tlv(0x03, bytes([1 if value else 0]))

    def _encode_integer(self, value: int | None) -> bytes:
        if value is None:
            return bytes([0x00])
        """Encode integer with appropriate size."""
        if -128 <= value <= 127:
            return self._encode_tlv(0x0F, value.to_bytes(1, 'big', signed=True))
        elif -32768 <= value <= 32767:
            return self._encode_tlv(0x10, value.to_bytes(2, 'big', signed=True))
        elif -2147483648 <= value <= 2147483647:
            return self._encode_tlv(0x11, value.to_bytes(4, 'big', signed=True))
        else:
            return self._encode_tlv(0x12, value.to_bytes(8, 'big', signed=True))

    def _encode_enum(self, value: int) -> bytes:
        """Encode enum (tag 0x16)."""
        return self._encode_tlv(0x16, value.to_bytes(1, 'big'))

    def _encode_float64(self, value: float) -> bytes:
        """Encode float64 (tag 0x11)."""
        return self._encode_tlv(0x11, struct.pack('>d', value))

    @staticmethod
    def _decode_float64(data: bytes) -> float:
        """Decode float64."""
        if len(data) == 8:
            return struct.unpack('>d', data)[0]
        elif len(data) == 4:
            return struct.unpack('>f', data)[0]
        return 0.0

    def _encode_string(self, value: str) -> bytes:
        """Encode UTF-8 string (tag 0x0C)."""
        return self._encode_tlv(0x0C, value.encode('utf-8'))

    def _encode_array(self, items: list) -> bytes:
        """Encode array (tag 0x01)."""
        inner = bytearray()
        for item in items:
            if hasattr(item, 'to_bytes'):
                inner += item.to_bytes()  # type: ignore[union-attr]
            elif isinstance(item, dict):
                inner += self._encode_dict_as_structure(item)
            elif isinstance(item, bool):
                inner += self._encode_boolean(item)
            elif isinstance(item, int):
                inner += self._encode_integer(item)
            elif isinstance(item, float):
                inner += self._encode_float64(item)
            elif isinstance(item, str):
                inner += self._encode_string(item)
            elif isinstance(item, bytes):
                inner += self._encode_octet_string(item)
            else:
                inner += self._encode_tlv(0x09, str(item).encode('utf-8'))
        return self._encode_tlv(0x01, bytes(inner))

    def _encode_structure(self, data: dict | None) -> bytes:
        if data is None: return bytes([0x00])
        """Encode structure (tag 0x02)."""
        return self._encode_tlv(0x02, self._encode_dict_as_structure(data))

    def _encode_dict_as_structure(self, d: dict) -> bytes:
        """Encode dict values as structure elements."""
        inner = bytearray()
        for key, value in d.items():
            if hasattr(value, 'to_bytes'):
                inner += value.to_bytes()  # type: ignore[union-attr]
            elif isinstance(value, bool):
                inner += self._encode_boolean(value)
            elif isinstance(value, int):
                inner += self._encode_integer(value)
            elif isinstance(value, float):
                inner += self._encode_float64(value)
            elif isinstance(value, str):
                inner += self._encode_string(value)
            elif isinstance(value, bytes):
                inner += self._encode_octet_string(value)
            elif isinstance(value, list):
                inner += self._encode_array(value)
            else:
                inner += self._encode_tlv(0x09, str(value).encode('utf-8'))
        return bytes(inner)

    @staticmethod
    def _decode_array(data: bytes) -> list:
        """Decode array elements."""
        items = []
        offset = 0
        while offset < len(data):
            tag = data[offset]
            length = data[offset + 1]
            off = offset + 2
            if length & 0x80:
                num_len = length & 0x7F
                length = int.from_bytes(data[off:off + num_len], 'big')
                off += num_len
            value = data[off:off + length]
            items.append(value)
            offset = off + length
        return items

    @staticmethod
    def _decode_structure(data: bytes) -> dict:
        """Decode structure elements to dict."""
        items = {}
        offset = 0
        idx = 0
        while offset < len(data):
            tag = data[offset]
            length = data[offset + 1]
            off = offset + 2
            if length & 0x80:
                num_len = length & 0x7F
                length = int.from_bytes(data[off:off + num_len], 'big')
                off += num_len
            value = data[off:off + length]
            items[idx] = value
            offset = off + length
            idx += 1
        return items

    def _encode_datetime(self, dt) -> bytes:
        """Encode datetime to DLMS octet-string (12 bytes)."""
        if dt is None:
            return self._encode_tlv(0x09, b'\x00' * 12)
        from datetime import datetime
        if isinstance(dt, datetime):
            data = bytearray(12)
            data[0] = dt.year >> 8
            data[1] = dt.year & 0xFF
            data[2] = dt.month
            data[3] = dt.day
            data[4] = dt.hour if hasattr(dt, 'hour') else 0xFF
            data[5] = dt.minute if hasattr(dt, 'minute') else 0xFF
            data[6] = dt.second if hasattr(dt, 'second') else 0xFF
            data[7] = 0x80  # deviation unspecified
            data[8] = 0x00
            data[9] = dt.weekday() if hasattr(dt, 'weekday') else 0xFF
            return self._encode_tlv(0x09, bytes(data))
        return self._encode_tlv(0x09, b'\x00' * 12)

    @staticmethod
    def _decode_datetime(data: bytes):
        """Decode DLMS datetime octet-string."""
        from datetime import datetime
        if len(data) < 9:
            return None
        try:
            return datetime(
                (data[0] << 8) | data[1], data[2], data[3],
                data[4] if data[4] != 0xFF else 0,
                data[5] if data[5] != 0xFF else 0,
                data[6] if data[6] != 0xFF else 0,
            )
        except (ValueError, IndexError):
            return None

    def _any_to_bytes(self, value) -> bytes:
        """Convert any value to bytes for serialization."""
        if value is None:
            return b''
        if hasattr(value, 'to_bytes'):
            return value.to_bytes()  # type: ignore[union-attr]
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        return str(value).encode('utf-8')

    def to_bytes(self) -> bytes:
        """Serialize all attributes to DLMS TLV byte sequence."""
        from dlms_cosem.cosem.base import CosemAttribute
        result = bytearray()
        # Attribute 1: logical_name (octet-string)
        result += self._encode_octet_string(self.logical_name.to_bytes())  # type: ignore[union-attr]
        # Attribute 3: mbus_port_reference
        result += self._encode_octet_string(self.mbus_port_reference.to_bytes())  # type: ignore[union-attr]
        # Attribute 4: capture_definition (array)
        result += self._encode_array(self.capture_definition)
        # Attribute 5: capture_period (integer)
        result += self._encode_integer(self.capture_period)
        # Attribute 6: primary_addresses (array)
        result += self._encode_array(self.primary_addresses)
        # Attribute 7: identification_number (string)
        result += self._encode_string(self.identification_number or '')
        # Attribute 8: manufacturer_id (string)
        result += self._encode_string(self.manufacturer_id or '')
        # Attribute 9: version (integer)
        result += self._encode_integer(self.version)
        # Attribute 10: device_type (integer)
        result += self._encode_integer(self.device_type)
        # Attribute 11: access_number (integer)
        result += self._encode_integer(self.access_number)
        # Attribute 12: status (integer)
        result += self._encode_integer(self.status)
        # Attribute 13: alarm (integer)
        result += self._encode_integer(self.alarm)
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MBusClient':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: mbus_port_reference
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['mbus_port_reference'] = Obis.from_bytes(value)
        # Attribute 4: capture_definition
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['capture_definition'] = cls._decode_array(value)
        # Attribute 5: capture_period
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['capture_period'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 6: primary_addresses
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['primary_addresses'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 7: identification_number
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['identification_number'] = value.decode('utf-8') if value else ''
        # Attribute 8: manufacturer_id
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['manufacturer_id'] = value.decode('utf-8') if value else ''
        # Attribute 9: version
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['version'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 10: device_type
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['device_type'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 11: access_number
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['access_number'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 12: status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 13: alarm
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['alarm'] = int.from_bytes(value, 'big', signed=True) if value else 0
        return cls(**kwargs)
