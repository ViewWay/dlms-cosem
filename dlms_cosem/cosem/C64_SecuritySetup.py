"""IC class 64 - Security Setup.

Defines security parameters for DLMS/COSEM communication.
Supports SM4-GMAC/SM4-GCM for Chinese national cryptography.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.3.17
Yellow Book: DLMS UA 1000-5
"""
from enum import IntEnum
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


class SecurityPolicy(IntEnum):
    """Security policy levels."""
    NONE = 0
    AUTHENTICATED_ONLY = 1
    ENCRYPTED_ONLY = 2
    AUTHENTICATED_ENCRYPTED = 3
    CERTIFICATE_BASED = 4
    DIGITALLY_SIGNED = 5


class CipherAlgorithm(IntEnum):
    """Supported cipher algorithms."""
    AES_128_GCM = 0
    AES_256_GCM = 1
    SM4_GCM = 2
    SM4_GMAC = 3


@attr.s(auto_attribs=True)
class SecuritySetup:
    """COSEM IC Security Setup (class_id=64).

    Attributes:
        1: logical_name (static)
        2: security_policy (static)
        3: security_suite (static) - 0~5
        4: cipher_algorithm (static)
        5: authentication_key (static) - handled via key management
        6: encryption_key (static)
        7: master_key (static)
        8: system_title (static, 8 bytes)
        9: certificate_info (static)
        10: legal_vote (static)
        11: ciphered_legal_vote (static)
    Methods:
        1: add_key
        2: remove_key
        3: change_key
        4: add_certificate
        5: remove_certificate
        6: add_legal_vote
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SECURITY_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    security_policy: SecurityPolicy = SecurityPolicy.AUTHENTICATED_ENCRYPTED
    security_suite: int = 0
    cipher_algorithm: CipherAlgorithm = CipherAlgorithm.AES_128_GCM
    authentication_key: Optional[bytes] = None
    encryption_key: Optional[bytes] = None
    master_key: Optional[bytes] = None
    system_title: Optional[bytes] = None
    certificate_info: Optional[bytes] = None
    legal_vote: Optional[bytes] = None
    ciphered_legal_vote: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="security_policy"),
        3: AttributeDescription(attribute_id=3, attribute_name="security_suite"),
        4: AttributeDescription(attribute_id=4, attribute_name="cipher_algorithm"),
        5: AttributeDescription(attribute_id=5, attribute_name="authentication_key"),
        6: AttributeDescription(attribute_id=6, attribute_name="encryption_key"),
        7: AttributeDescription(attribute_id=7, attribute_name="master_key"),
        8: AttributeDescription(attribute_id=8, attribute_name="system_title"),
        9: AttributeDescription(attribute_id=9, attribute_name="certificate_info"),
        10: AttributeDescription(attribute_id=10, attribute_name="legal_vote"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        11: AttributeDescription(attribute_id=11, attribute_name="ciphered_legal_vote"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "add_key", 2: "remove_key", 3: "change_key",
        4: "add_certificate", 5: "remove_certificate", 6: "add_legal_vote",
    }

    def add_key(self, key: bytes) -> None:
        pass

    def remove_key(self, key_id: int) -> None:
        pass

    def change_key(self, key_id: int, new_key: bytes) -> None:
        pass

    def add_certificate(self, certificate: bytes) -> None:
        pass

    def remove_certificate(self, cert_id: int) -> None:
        pass

    def add_legal_vote(self, vote: bytes) -> None:
        pass

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
        # Attribute 3: security_policy
        result += self._encode_octet_string(self._any_to_bytes(self.security_policy))
        # Attribute 4: security_suite (integer)
        result += self._encode_integer(self.security_suite)
        # Attribute 5: cipher_algorithm
        result += self._encode_octet_string(self._any_to_bytes(self.cipher_algorithm))
        # Attribute 6: authentication_key (octet-string)
        result += self._encode_octet_string(self.authentication_key or b'')
        # Attribute 7: encryption_key (octet-string)
        result += self._encode_octet_string(self.encryption_key or b'')
        # Attribute 8: master_key (octet-string)
        result += self._encode_octet_string(self.master_key or b'')
        # Attribute 9: system_title (octet-string)
        result += self._encode_octet_string(self.system_title or b'')
        # Attribute 10: certificate_info (octet-string)
        result += self._encode_octet_string(self.certificate_info or b'')
        # Attribute 11: legal_vote (octet-string)
        result += self._encode_octet_string(self.legal_vote or b'')
        # Attribute 12: ciphered_legal_vote (octet-string)
        result += self._encode_octet_string(self.ciphered_legal_vote or b'')
        return bytes(result)
    @classmethod
    def from_bytes(cls, data: bytes) -> 'SecuritySetup':
        """Deserialize from DLMS TLV byte sequence."""
        from dlms_cosem.cosem.obis import Obis
        kwargs = {}
        offset = 0

        # Attribute 1: logical_name
        tag, value, offset = cls._decode_tlv(data, offset)
        kwargs['logical_name'] = Obis.from_bytes(value)
        # Attribute 3: security_policy
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['security_policy'] = value
        # Attribute 4: security_suite
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['security_suite'] = int.from_bytes(value, 'big', signed=True) if value else 0
        # Attribute 5: cipher_algorithm
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['cipher_algorithm'] = value
        # Attribute 6: authentication_key
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['authentication_key'] = value
        # Attribute 7: encryption_key
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['encryption_key'] = value
        # Attribute 8: master_key
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['master_key'] = value
        # Attribute 9: system_title
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['system_title'] = value
        # Attribute 10: certificate_info
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['certificate_info'] = value
        # Attribute 11: legal_vote
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['legal_vote'] = value
        # Attribute 12: ciphered_legal_vote
        if offset < len(data):
            tag, value, offset = cls._decode_tlv(data, offset)
            kwargs['ciphered_legal_vote'] = value
        return cls(**kwargs)
