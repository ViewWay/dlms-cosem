"""IC class 66 - MeasurementDataMonitoring.

Measurement Data Monitoring - monitors measurement data with trigger-based capture.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=66
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
import struct


@attr.s(auto_attribs=True)
class MeasurementDataMonitoring:
    """COSEM IC MeasurementDataMonitoring (class_id=66).

    Attributes:
        1: logical_name (static)
        2: status (dynamic)
        3: trigger_source (dynamic)
        4: sampling_rate (dynamic)
        5: number_of_samples_before_trigger (dynamic)
        6: number_of_samples_after_trigger (dynamic)
        7: trigger_time (dynamic)
        8: scaler_unit (dynamic)
    Methods:
        1: reset
        2: capture
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MEASUREMENT_DATA_MONITORING
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    status: Optional[int] = 0
    trigger_source: Optional[int] = 0
    sampling_rate: Optional[int] = 0
    number_of_samples_before_trigger: Optional[int] = 0
    number_of_samples_after_trigger: Optional[int] = 0
    trigger_time: Optional[bytes] = None
    scaler_unit: Optional[Any] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'status', 3: 'trigger_source', 4: 'sampling_rate', 5: 'number_of_samples_before_trigger', 6: 'number_of_samples_after_trigger', 7: 'trigger_time', 8: 'scaler_unit'}
    METHODS: ClassVar[Dict[int, str]] = {1: 'reset', 2: 'capture'}

    def reset(self) -> None:
        """Method 1: reset."""

    def capture(self) -> None:
        """Method 2: capture."""

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
        # Attribute 3: status (integer)
        result += self._encode_integer(self.status)
        # Attribute 4: trigger_source (integer)
        result += self._encode_integer(self.trigger_source)
        # Attribute 5: sampling_rate (integer)
        result += self._encode_integer(self.sampling_rate)
        # Attribute 6: number_of_samples_before_trigger (integer)
        result += self._encode_integer(self.number_of_samples_before_trigger)
        # Attribute 7: number_of_samples_after_trigger (integer)
        result += self._encode_integer(self.number_of_samples_after_trigger)
        # Attribute 8: trigger_time (octet-string)
        result += self._encode_octet_string(self.trigger_time or b'')
        # Attribute 9: scaler_unit
        result += self._encode_octet_string(self._any_to_bytes(self.scaler_unit))
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MeasurementDataMonitoring':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 4: trigger_source
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['trigger_source'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 5: sampling_rate
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['sampling_rate'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 6: number_of_samples_before_trigger
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['number_of_samples_before_trigger'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 7: number_of_samples_after_trigger
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['number_of_samples_after_trigger'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 8: trigger_time
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['trigger_time'] = value
        # Attribute 9: scaler_unit
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['scaler_unit'] = value
        return cls(**kwargs)
