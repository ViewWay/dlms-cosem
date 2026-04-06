"""IC class 63 - Status Mapping.

Maps internal status codes to external representations.
Used for standardizing status reporting across different devices.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.63
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class StatusMappingEntry:
    """A single status mapping entry."""
    internal_status: int
    external_status: int
    description: str


@attr.s(auto_attribs=True)
class StatusMapping:
    """COSEM IC Status Mapping (class_id=63).

    Attributes:
        1: logical_name (static)
        2: mappings (dynamic, array of StatusMappingEntry)
        3: default_external_status (dynamic, unsigned)
    Methods:
        1: map_status
        2: add_mapping
        3: remove_mapping
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.STATUS_MAPPING
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mappings: List[StatusMappingEntry] = attr.ib(factory=list)
    default_external_status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="mappings"),
        3: AttributeDescription(attribute_id=3, attribute_name="default_external_status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "map_status", 2: "add_mapping", 3: "remove_mapping"}

    def add_mapping(self, internal_status: int, external_status: int, description: str) -> None:
        """Method 2: Add a status mapping."""
        entry = StatusMappingEntry(
            internal_status=internal_status,
            external_status=external_status,
            description=description,
        )
        self.mappings.append(entry)

    def remove_mapping(self, internal_status: int) -> bool:
        """Method 3: Remove a status mapping."""
        for i, mapping in enumerate(self.mappings):
            if mapping.internal_status == internal_status:
                self.mappings.pop(i)
                return True
        return False

    def map_status(self, internal_status: int) -> int:
        """Method 1: Map internal status to external status."""
        for mapping in self.mappings:
            if mapping.internal_status == internal_status:
                return mapping.external_status
        return self.default_external_status

    def get_mapping_by_internal_status(self, internal_status: int) -> StatusMappingEntry:
        """Get mapping entry by internal status."""
        for mapping in self.mappings:
            if mapping.internal_status == internal_status:
                return mapping
        return None

    def set_default_external_status(self, status: int) -> None:
        """Set the default external status."""
        self.default_external_status = status

    def get_mapping_count(self) -> int:
        """Get the number of mappings."""
        return len(self.mappings)

    def clear_mappings(self) -> None:
        """Clear all mappings."""
        self.mappings = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
