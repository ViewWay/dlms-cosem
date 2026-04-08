"""IC class 101 - ZigbeeSASStartup.

ZigBee SAS Startup - ZigBee Smart Energy Profile startup configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=101
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
import struct


@attr.s(auto_attribs=True)
class ZigbeeSASStartup:
    """COSEM IC ZigbeeSASStartup (class_id=101).

    Attributes:
        1: logical_name (static)
        2: startup_control (dynamic)
        3: channel_mask (dynamic)
        4: scan_duration (dynamic)
        5: scan_attempts (dynamic)
        6: scan_attempts_timeout (dynamic)
        7: channel (dynamic)
        8: security_level (dynamic)
        9: preconfigured_link_key (dynamic)
        10: network_key (dynamic)
        11: network_key_enable (dynamic)
        12: use_insecure_join (dynamic)
        13: permit_duration (dynamic)
        14: device_timeout (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_SAS_STARTUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    startup_control: Optional[int] = 0
    channel_mask: Optional[int] = 0
    scan_duration: Optional[int] = 0
    scan_attempts: Optional[int] = 0
    scan_attempts_timeout: Optional[int] = 0
    channel: Optional[int] = 0
    security_level: Optional[int] = 0
    preconfigured_link_key: Optional[bytes] = None
    network_key: Optional[bytes] = None
    network_key_enable: Optional[bool] = False
    use_insecure_join: Optional[bool] = False
    permit_duration: Optional[int] = 0
    device_timeout: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'startup_control', 3: 'channel_mask', 4: 'scan_duration', 5: 'scan_attempts', 6: 'scan_attempts_timeout', 7: 'channel', 8: 'security_level', 9: 'preconfigured_link_key', 10: 'network_key', 11: 'network_key_enable', 12: 'use_insecure_join', 13: 'permit_duration', 14: 'device_timeout'}
    METHODS: ClassVar[Dict[int, str]] = {}

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
        # Attribute 3: startup_control (integer)
        result += self._encode_integer(self.startup_control)
        # Attribute 4: channel_mask (integer)
        result += self._encode_integer(self.channel_mask)
        # Attribute 5: scan_duration (integer)
        result += self._encode_integer(self.scan_duration)
        # Attribute 6: scan_attempts (integer)
        result += self._encode_integer(self.scan_attempts)
        # Attribute 7: scan_attempts_timeout (integer)
        result += self._encode_integer(self.scan_attempts_timeout)
        # Attribute 8: channel (integer)
        result += self._encode_integer(self.channel)
        # Attribute 9: security_level (integer)
        result += self._encode_integer(self.security_level)
        # Attribute 10: preconfigured_link_key (octet-string)
        result += self._encode_octet_string(self.preconfigured_link_key or b'')
        # Attribute 11: network_key (octet-string)
        result += self._encode_octet_string(self.network_key or b'')
        # Attribute 12: network_key_enable (boolean)
        result += self._encode_boolean(self.network_key_enable)
        # Attribute 13: use_insecure_join (boolean)
        result += self._encode_boolean(self.use_insecure_join)
        # Attribute 14: permit_duration (integer)
        result += self._encode_integer(self.permit_duration)
        # Attribute 15: device_timeout (integer)
        result += self._encode_integer(self.device_timeout)
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ZigbeeSASStartup':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: startup_control
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['startup_control'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 4: channel_mask
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['channel_mask'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 5: scan_duration
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['scan_duration'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 6: scan_attempts
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['scan_attempts'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 7: scan_attempts_timeout
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['scan_attempts_timeout'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 8: channel
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['channel'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 9: security_level
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['security_level'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 10: preconfigured_link_key
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['preconfigured_link_key'] = value
        # Attribute 11: network_key
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['network_key'] = value
        # Attribute 12: network_key_enable
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['network_key_enable'] = bool(value[0]) if value else False
        # Attribute 13: use_insecure_join
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['use_insecure_join'] = bool(value[0]) if value else False
        # Attribute 14: permit_duration
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['permit_duration'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 15: device_timeout
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['device_timeout'] = int.from_bytes(value, 'big', signed=True) if value else 0
        return cls(**kwargs)
