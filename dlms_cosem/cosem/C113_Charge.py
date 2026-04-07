"""IC class 113 - Charge.

Charge management for billing and tariffication.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.6.3
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription
import struct


@attr.s(auto_attribs=True)
class Charge:
    """COSEM IC Charge (class_id=113).

    Attributes:
        1: logical_name (static)
        2: total_amount (dynamic) - Total charge amount
        3: charge_type (dynamic) - Type of charge
        4: priority (dynamic) - Priority level
        5: unit_charge (dynamic) - Unit charge rate
        6: unit_charge_active (dynamic) - Active unit charge rate
        7: last_execution_time (dynamic) - Time of last execution
        8: execution_period (dynamic) - Period between executions
        9: total_amount_published (dynamic) - Published total amount
    Methods:
        1: reset
        2: update_total_amount
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CHARGE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    total_amount: float = 0.0
    charge_type: int = 0
    priority: int = 0
    unit_charge: float = 0.0
    unit_charge_active: float = 0.0
    last_execution_time: Optional[bytes] = None
    execution_period: int = 0
    total_amount_published: float = 0.0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="total_amount"),
        3: AttributeDescription(attribute_id=3, attribute_name="charge_type"),
        4: AttributeDescription(attribute_id=4, attribute_name="priority"),
        5: AttributeDescription(attribute_id=5, attribute_name="unit_charge"),
        6: AttributeDescription(attribute_id=6, attribute_name="unit_charge_active"),
        7: AttributeDescription(attribute_id=7, attribute_name="last_execution_time"),
        8: AttributeDescription(attribute_id=8, attribute_name="execution_period"),
        9: AttributeDescription(attribute_id=9, attribute_name="total_amount_published"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "update_total_amount",
    }

    def reset(self) -> None:
        """Method 1: Reset charge to defaults."""
        self.total_amount = 0.0
        self.unit_charge_active = 0.0
        self.last_execution_time = None
        self.total_amount_published = 0.0

    def update_total_amount(self, amount: float) -> None:
        """Method 2: Update total charge amount."""
        self.total_amount += amount

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def calculate_charge(self, units: float) -> float:
        """Calculate charge for given units."""
        return units * self.unit_charge_active


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
                inner += item.to_bytes()
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
                inner += value.to_bytes()
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
            return value.to_bytes()
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        return str(value).encode('utf-8')

    def to_bytes(self) -> bytes:
        """Serialize all attributes to DLMS TLV byte sequence."""
        from dlms_cosem.cosem.base import CosemAttribute
        result = bytearray()
        # Attribute 1: logical_name (octet-string)
        result += self._encode_octet_string(self.logical_name.to_bytes())
        # Attribute 3: total_amount (float64)
        result += self._encode_float64(self.total_amount)
        # Attribute 4: charge_type (integer)
        result += self._encode_integer(self.charge_type)
        # Attribute 5: priority (integer)
        result += self._encode_integer(self.priority)
        # Attribute 6: unit_charge (float64)
        result += self._encode_float64(self.unit_charge)
        # Attribute 7: unit_charge_active (float64)
        result += self._encode_float64(self.unit_charge_active)
        # Attribute 8: last_execution_time (octet-string)
        result += self._encode_octet_string(self.last_execution_time or b'')
        # Attribute 9: execution_period (integer)
        result += self._encode_integer(self.execution_period)
        # Attribute 10: total_amount_published (float64)
        result += self._encode_float64(self.total_amount_published)
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Charge':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: total_amount
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['total_amount'] = cls._decode_float64(value) if value else 0.0
        # Attribute 4: charge_type
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['charge_type'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 5: priority
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['priority'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 6: unit_charge
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['unit_charge'] = cls._decode_float64(value) if value else 0.0
        # Attribute 7: unit_charge_active
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['unit_charge_active'] = cls._decode_float64(value) if value else 0.0
        # Attribute 8: last_execution_time
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['last_execution_time'] = value
        # Attribute 9: execution_period
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['execution_period'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 10: total_amount_published
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['total_amount_published'] = cls._decode_float64(value) if value else 0.0
        return cls(**kwargs)
