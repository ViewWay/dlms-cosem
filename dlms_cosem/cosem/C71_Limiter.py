"""IC class 71 - Limiter.

Threshold monitoring and limiting for values.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.9
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription
import struct


@attr.s(auto_attribs=True)
class Limiter:
    """COSEM IC Limiter (class_id=71).

    Attributes:
        1: logical_name (static)
        2: monitored_value (dynamic) - Value being monitored
        3: threshold_active (dynamic) - Active threshold value
        4: threshold_normal (dynamic) - Normal threshold value
        5: threshold_emergency (dynamic) - Emergency threshold value
        6: min_over_threshold_duration (dynamic) - Min duration over threshold
        7: min_under_threshold_duration (dynamic) - Min duration under threshold
        8: emergency_profile (dynamic) - Emergency profile settings
        9: emergency_profile_group (dynamic) - Emergency profile group
        10: emergency_profile_active (dynamic) - Is emergency profile active
        11: action_over_threshold (dynamic) - Action when over threshold
        12: action_under_threshold (dynamic) - Action when under threshold
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LIMITER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    monitored_value: Optional[Dict[str, Any]] = None
    threshold_active: float = 0.0
    threshold_normal: float = 0.0
    threshold_emergency: float = 0.0
    min_over_threshold_duration: int = 0
    min_under_threshold_duration: int = 0
    emergency_profile: Optional[Dict[str, Any]] = None
    emergency_profile_group: int = 0
    emergency_profile_active: bool = False
    action_over_threshold: Optional[Dict[str, Any]] = None
    action_under_threshold: Optional[Dict[str, Any]] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="monitored_value"),
        3: AttributeDescription(attribute_id=3, attribute_name="threshold_active"),
        4: AttributeDescription(attribute_id=4, attribute_name="threshold_normal"),
        5: AttributeDescription(attribute_id=5, attribute_name="threshold_emergency"),
        6: AttributeDescription(attribute_id=6, attribute_name="min_over_threshold_duration"),
        7: AttributeDescription(attribute_id=7, attribute_name="min_under_threshold_duration"),
        8: AttributeDescription(attribute_id=8, attribute_name="emergency_profile"),
        9: AttributeDescription(attribute_id=9, attribute_name="emergency_profile_group"),
        10: AttributeDescription(attribute_id=10, attribute_name="emergency_profile_active"),
        11: AttributeDescription(attribute_id=11, attribute_name="action_over_threshold"),
        12: AttributeDescription(attribute_id=12, attribute_name="action_under_threshold"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset limiter to defaults."""
        self.threshold_active = 0.0
        self.threshold_normal = 0.0
        self.threshold_emergency = 0.0
        self.min_over_threshold_duration = 0
        self.min_under_threshold_duration = 0
        self.emergency_profile_active = False

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def is_over_threshold(self, value: float) -> bool:
        """Check if value exceeds active threshold."""
        return value > self.threshold_active

    def is_under_threshold(self, value: float) -> bool:
        """Check if value is below threshold."""
        return value < self.threshold_normal


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

    def _encode_boolean(self, value: bool) -> bytes:
        """Encode boolean (tag 0x03)."""
        return self._encode_tlv(0x03, bytes([1 if value else 0]))

    def _encode_integer(self, value: int) -> bytes:
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

    def _encode_structure(self, data: dict) -> bytes:
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
        # Attribute 3: monitored_value (structure)
        result += self._encode_structure(self.monitored_value)
        # Attribute 4: threshold_active (float64)
        result += self._encode_float64(self.threshold_active)
        # Attribute 5: threshold_normal (float64)
        result += self._encode_float64(self.threshold_normal)
        # Attribute 6: threshold_emergency (float64)
        result += self._encode_float64(self.threshold_emergency)
        # Attribute 7: min_over_threshold_duration (integer)
        result += self._encode_integer(self.min_over_threshold_duration)
        # Attribute 8: min_under_threshold_duration (integer)
        result += self._encode_integer(self.min_under_threshold_duration)
        # Attribute 9: emergency_profile (structure)
        result += self._encode_structure(self.emergency_profile)
        # Attribute 10: emergency_profile_group (integer)
        result += self._encode_integer(self.emergency_profile_group)
        # Attribute 11: emergency_profile_active (boolean)
        result += self._encode_boolean(self.emergency_profile_active)
        # Attribute 12: action_over_threshold (structure)
        result += self._encode_structure(self.action_over_threshold)
        # Attribute 13: action_under_threshold (structure)
        result += self._encode_structure(self.action_under_threshold)
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Limiter':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: monitored_value
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['monitored_value'] = cls._decode_structure(value)
        # Attribute 4: threshold_active
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['threshold_active'] = cls._decode_float64(value) if value else 0.0
        # Attribute 5: threshold_normal
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['threshold_normal'] = cls._decode_float64(value) if value else 0.0
        # Attribute 6: threshold_emergency
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['threshold_emergency'] = cls._decode_float64(value) if value else 0.0
        # Attribute 7: min_over_threshold_duration
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['min_over_threshold_duration'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 8: min_under_threshold_duration
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['min_under_threshold_duration'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 9: emergency_profile
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['emergency_profile'] = cls._decode_structure(value)
        # Attribute 10: emergency_profile_group
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['emergency_profile_group'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 11: emergency_profile_active
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['emergency_profile_active'] = bool(value[0]) if value else False
        # Attribute 12: action_over_threshold
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['action_over_threshold'] = cls._decode_structure(value)
        # Attribute 13: action_under_threshold
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['action_under_threshold'] = cls._decode_structure(value)
        return cls(**kwargs)

    def check_threshold(self, value: float) -> str:
        """Check value against all configured thresholds.

        Returns: 'normal', 'emergency', 'over_threshold', or 'under_threshold'.
        """
        if self.threshold_emergency > 0 and value >= self.threshold_emergency:
            return 'emergency'
        if self.threshold_active > 0 and value > self.threshold_active:
            return 'over_threshold'
        if self.threshold_normal > 0 and value < self.threshold_normal:
            return 'under_threshold'
        return 'normal'

    def activate_emergency(self) -> bool:
        """Activate the emergency profile. Returns True if successful."""
        if self.emergency_profile is None:
            return False
        self.emergency_profile_active = True
        return True

    def deactivate_emergency(self) -> None:
        """Deactivate the emergency profile."""
        self.emergency_profile_active = False

    def evaluate_thresholds(self, value: float, duration_seconds: float) -> Optional[str]:
        """Evaluate thresholds with minimum duration consideration.

        Returns: 'over_threshold', 'under_threshold', or None.
        """
        if value > self.threshold_active and self.threshold_active > 0:
            if duration_seconds >= self.min_over_threshold_duration:
                return 'over_threshold'
        elif value < self.threshold_normal and self.threshold_normal > 0:
            if duration_seconds >= self.min_under_threshold_duration:
                return 'under_threshold'
        return None
