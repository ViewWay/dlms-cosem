"""IC class 20 - Activity Calendar.

Defines activity periods and special days for tariff calculation.
Used in complex tariff schemes with calendar-based rates.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.20
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription
import struct


@attr.s(auto_attribs=True)
class ActivityPeriod:
    """An activity period in the calendar."""
    start_date: str  # Format: MM-DD
    end_date: str    # Format: MM-DD
    activity_id: int
    description: str


@attr.s(auto_attribs=True)
class ActivityCalendar:
    """COSEM IC Activity Calendar (class_id=20).

    Attributes:
        1: logical_name (static)
        2: activity_periods (dynamic, array of ActivityPeriod)
        3: calendar_name (dynamic, visible-string)
    Methods:
        1: add_period
        2: remove_period
        3: get_activity_for_date
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ACTIVITY_CALENDAR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    activity_periods: List[ActivityPeriod] = attr.ib(factory=list)
    calendar_name: str = ""

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="activity_periods"),
        3: AttributeDescription(attribute_id=3, attribute_name="calendar_name"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "add_period", 2: "remove_period", 3: "get_activity_for_date"}

    def add_period(self, start_date: str, end_date: str, activity_id: int, description: str = "") -> None:
        """Method 1: Add an activity period."""
        period = ActivityPeriod(
            start_date=start_date,
            end_date=end_date,
            activity_id=activity_id,
            description=description,
        )
        self.activity_periods.append(period)

    def remove_period(self, activity_id: int) -> bool:
        """Method 2: Remove an activity period by activity ID."""
        for i, period in enumerate(self.activity_periods):
            if period.activity_id == activity_id:
                self.activity_periods.pop(i)
                return True
        return False

    def get_activity_for_date(self, date_str: str) -> int:
        """Method 3: Get activity ID for a given date (format: MM-DD)."""
        for period in self.activity_periods:
            # Simple string comparison for date ranges
            if period.start_date <= date_str <= period.end_date:
                return period.activity_id
        return 0  # Default activity

    def set_calendar_name(self, name: str) -> None:
        """Set the calendar name."""
        self.calendar_name = name

    def get_period_count(self) -> int:
        """Get the number of activity periods."""
        return len(self.activity_periods)

    def get_period_by_activity_id(self, activity_id: int) -> ActivityPeriod:
        """Get period by activity ID."""
        for period in self.activity_periods:
            if period.activity_id == activity_id:
                return period
        return None

    def clear_periods(self) -> None:
        """Clear all activity periods."""
        self.activity_periods = []

    def is_date_in_period(self, date_str: str, activity_id: int) -> bool:
        """Check if a date is in a specific activity period."""
        period = self.get_period_by_activity_id(activity_id)
        if period is None:
            return False
        return period.start_date <= date_str <= period.end_date

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
            return None  # type: ignore[return-value]
        try:
            return datetime(
                (data[0] << 8) | data[1], data[2], data[3],
                data[4] if data[4] != 0xFF else 0,
                data[5] if data[5] != 0xFF else 0,
                data[6] if data[6] != 0xFF else 0,
            )
        except (ValueError, IndexError):
            return None  # type: ignore[return-value]

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
        # Attribute 3: activity_periods (array)
        result += self._encode_array(self.activity_periods)
        # Attribute 4: calendar_name (string)
        result += self._encode_string(self.calendar_name or '')
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ActivityCalendar':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: activity_periods
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['activity_periods'] = cls._decode_array(value)
        # Attribute 4: calendar_name
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['calendar_name'] = value.decode('utf-8') if value else ''
        return cls(**kwargs)
