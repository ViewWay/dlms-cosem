"""IC class 151 - LTEMonitoring.

LTE Monitoring - provides LTE network monitoring information.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=151
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
import struct


@attr.s(auto_attribs=True)
class LTEMonitoring:
    """COSEM IC LTEMonitoring (class_id=151).

    Attributes:
        1: logical_name (static)
        2: operator (dynamic)
        3: signal_strength (dynamic)
        4: noise_level (dynamic)
        5: status (dynamic)
        6: circuit_switch_status (dynamic)
        7: packet_switch_status (dynamic)
        8: cell_id (dynamic)
        9: location_area (dynamic)
        10: vci (dynamic)
        11: mcc (dynamic)
        12: mnc (dynamic)
        13: base_station_id (dynamic)
        14: sim_status (dynamic)
        15: roaming_status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LTE_MONITORING
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    operator: Optional[str] = ''
    signal_strength: Optional[int] = 0
    noise_level: Optional[int] = 0
    status: Optional[int] = 0
    circuit_switch_status: Optional[int] = 0
    packet_switch_status: Optional[int] = 0
    cell_id: Optional[int] = 0
    location_area: Optional[int] = 0
    vci: Optional[int] = 0
    mcc: Optional[int] = 0
    mnc: Optional[int] = 0
    base_station_id: Optional[int] = 0
    sim_status: Optional[int] = 0
    roaming_status: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'operator', 3: 'signal_strength', 4: 'noise_level', 5: 'status', 6: 'circuit_switch_status', 7: 'packet_switch_status', 8: 'cell_id', 9: 'location_area', 10: 'vci', 11: 'mcc', 12: 'mnc', 13: 'base_station_id', 14: 'sim_status', 15: 'roaming_status'}
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
        # Attribute 3: operator (string)
        result += self._encode_string(self.operator or '')
        # Attribute 4: signal_strength (integer)
        result += self._encode_integer(self.signal_strength)
        # Attribute 5: noise_level (integer)
        result += self._encode_integer(self.noise_level)
        # Attribute 6: status (integer)
        result += self._encode_integer(self.status)
        # Attribute 7: circuit_switch_status (integer)
        result += self._encode_integer(self.circuit_switch_status)
        # Attribute 8: packet_switch_status (integer)
        result += self._encode_integer(self.packet_switch_status)
        # Attribute 9: cell_id (integer)
        result += self._encode_integer(self.cell_id)
        # Attribute 10: location_area (integer)
        result += self._encode_integer(self.location_area)
        # Attribute 11: vci (integer)
        result += self._encode_integer(self.vci)
        # Attribute 12: mcc (integer)
        result += self._encode_integer(self.mcc)
        # Attribute 13: mnc (integer)
        result += self._encode_integer(self.mnc)
        # Attribute 14: base_station_id (integer)
        result += self._encode_integer(self.base_station_id)
        # Attribute 15: sim_status (integer)
        result += self._encode_integer(self.sim_status)
        # Attribute 16: roaming_status (integer)
        result += self._encode_integer(self.roaming_status)
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'LTEMonitoring':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: operator
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['operator'] = value.decode('utf-8') if value else ''
        # Attribute 4: signal_strength
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['signal_strength'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 5: noise_level
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['noise_level'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 6: status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 7: circuit_switch_status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['circuit_switch_status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 8: packet_switch_status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['packet_switch_status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 9: cell_id
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['cell_id'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 10: location_area
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['location_area'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 11: vci
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['vci'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 12: mcc
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['mcc'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 13: mnc
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['mnc'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 14: base_station_id
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['base_station_id'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 15: sim_status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['sim_status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 16: roaming_status
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['roaming_status'] = int.from_bytes(value, 'big', signed=True) if value else 0
        return cls(**kwargs)
