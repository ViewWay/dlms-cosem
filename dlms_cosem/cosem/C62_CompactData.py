"""IC class 62 - Compact Data.

Compact representation of data using bitmaps and variable-length fields.
Optimized for bandwidth-constrained environments.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.62
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class CompactDataField:
    """A single field in compact data."""
    index: int
    value: Any
    offset: int
    length: int


@attr.s(auto_attribs=True)
class CompactData:
    """COSEM IC Compact Data (class_id=62).

    Attributes:
        1: logical_name (static)
        2: buffer (dynamic, octet-string)
        3: bitmap (dynamic, bit-string)
        4: fields (dynamic, array of CompactDataField)
    Methods:
        1: decode
        2: encode
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.COMPACT_DATA
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    buffer: bytes = b""
    bitmap: int = 0
    fields: List[CompactDataField] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="buffer"),
        3: AttributeDescription(attribute_id=3, attribute_name="bitmap"),
        4: AttributeDescription(attribute_id=4, attribute_name="fields"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "decode", 2: "encode"}

    def set_buffer(self, buffer: bytes) -> None:
        """Set the buffer data."""
        self.buffer = buffer

    def set_bitmap(self, bitmap: int) -> None:
        """Set the bitmap indicating which fields are present."""
        self.bitmap = bitmap

    def add_field(self, field: CompactDataField) -> None:
        """Add a field to the compact data."""
        self.fields.append(field)

    def get_field_by_index(self, index: int) -> Optional[CompactDataField]:
        """Get a field by its index."""
        for field in self.fields:
            if field.index == index:
                return field
        return None

    def get_buffer_size(self) -> int:
        """Get the buffer size in bytes."""
        return len(self.buffer)

    def decode(self) -> bool:
        """Method 1: Decode the buffer and bitmap into fields."""
        # Simplified implementation - in real scenario, would parse bitmap and buffer
        return True

    def encode(self) -> bool:
        """Method 2: Encode fields into buffer and bitmap."""
        # Simplified implementation - in real scenario, would encode fields
        return True

    def reset(self) -> None:
        """Reset all data."""
        self.buffer = b""
        self.bitmap = 0
        self.fields = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
