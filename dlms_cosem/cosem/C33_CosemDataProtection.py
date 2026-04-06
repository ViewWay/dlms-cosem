"""IC class 30 - COSEM Data Protection.

Protects COSEM objects from unauthorized access and modification.
Implements access control and data integrity checks.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.30
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ProtectedObject:
    """A protected COSEM object."""
    class_id: int
    logical_name: bytes
    read_protection: int = 0
    write_protection: int = 0


@attr.s(auto_attribs=True)
class CosemDataProtection:
    """COSEM IC COSEM Data Protection (class_id=30).

    Attributes:
        1: logical_name (static)
        2: protected_objects (dynamic, array of ProtectedObject)
        3: protection_level (dynamic, unsigned)
        4: protection_enabled (dynamic, boolean)
    Methods:
        1: add_protection
        2: remove_protection
        3: check_access
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.COSEM_DATA_PROTECTION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    protected_objects: List[ProtectedObject] = attr.ib(factory=list)
    protection_level: int = 1
    protection_enabled: bool = True

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="protected_objects"),
        3: AttributeDescription(attribute_id=3, attribute_name="protection_level"),
        4: AttributeDescription(attribute_id=4, attribute_name="protection_enabled"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "add_protection", 2: "remove_protection", 3: "check_access"}

    def add_protection(self, class_id: int, logical_name: bytes, read_prot: int = 1, write_prot: int = 2) -> None:
        """Method 1: Add protection for a COSEM object."""
        obj = ProtectedObject(
            class_id=class_id,
            logical_name=logical_name,
            read_protection=read_prot,
            write_protection=write_prot,
        )
        self.protected_objects.append(obj)

    def remove_protection(self, class_id: int, logical_name: bytes) -> bool:
        """Method 2: Remove protection for a COSEM object."""
        for i, obj in enumerate(self.protected_objects):
            if obj.class_id == class_id and obj.logical_name == logical_name:
                self.protected_objects.pop(i)
                return True
        return False

    def check_access(self, class_id: int, logical_name: bytes, access_type: str, user_level: int) -> bool:
        """Method 3: Check if access is allowed."""
        if not self.protection_enabled:
            return True

        for obj in self.protected_objects:
            if obj.class_id == class_id and obj.logical_name == logical_name:
                if access_type == "read":
                    return user_level >= obj.read_protection
                elif access_type == "write":
                    return user_level >= obj.write_protection
                return False

        # No protection specified for this object
        return True

    def set_protection_level(self, level: int) -> None:
        """Set the global protection level."""
        self.protection_level = max(0, min(255, level))

    def set_protection_enabled(self, enabled: bool) -> None:
        """Enable or disable protection."""
        self.protection_enabled = enabled

    def get_object_protection(self, class_id: int, logical_name: bytes) -> ProtectedObject:
        """Get protection for a specific object."""
        for obj in self.protected_objects:
            if obj.class_id == class_id and obj.logical_name == logical_name:
                return obj
        return None

    def get_protected_object_count(self) -> int:
        """Get the number of protected objects."""
        return len(self.protected_objects)

    def clear_protections(self) -> None:
        """Clear all protections."""
        self.protected_objects = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
