"""IC class 29 - Value Table.

A table for storing multiple values with associated descriptors.
Used for configurable data storage and lookup tables.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.29
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ValueEntry:
    """A single entry in the value table."""
    index: int
    value: Any
    timestamp: Optional[bytes] = None  # DLMS datetime


@attr.s(auto_attribs=True)
class ValueDescriptor:
    """Descriptor for a value in the table."""
    index: int
    description: str
    unit: int
    scaler: int


@attr.s(auto_attribs=True)
class ValueTable:
    """COSEM IC Value Table (class_id=29).

    Attributes:
        1: logical_name (static)
        2: values (dynamic, array of ValueEntry)
        3: value_descriptors (dynamic, array of ValueDescriptor)
    Methods:
        None typically
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.VALUE_TABLE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    values: List[ValueEntry] = attr.ib(factory=list)
    descriptors: List[ValueDescriptor] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="values"),
        3: AttributeDescription(attribute_id=3, attribute_name="value_descriptors"),
    }

    def add_value(self, entry: ValueEntry) -> None:
        """Add a value entry to the table."""
        self.values.append(entry)

    def add_descriptor(self, descriptor: ValueDescriptor) -> None:
        """Add a descriptor to the table."""
        self.descriptors.append(descriptor)

    def remove_value(self, index: int) -> Optional[ValueEntry]:
        """Remove a value entry by index."""
        if 0 <= index < len(self.values):
            return self.values.pop(index)
        return None

    def get_value_by_index(self, index: int) -> Optional[ValueEntry]:
        """Get a value entry by its index."""
        for entry in self.values:
            if entry.index == index:
                return entry
        return None

    def get_descriptor_by_index(self, index: int) -> Optional[ValueDescriptor]:
        """Get a descriptor by its index."""
        for desc in self.descriptors:
            if desc.index == index:
                return desc
        return None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
