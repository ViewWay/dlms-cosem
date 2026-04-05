"""IC class 17 - SAP Assignment.

Manages Service Access Point (SAP) assignments for DLMS connections.
Defines which SAPs are used for different application contexts.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.17
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class SapAssignmentEntry:
    """A SAP assignment entry."""
    sap_id: int
    application_context: bytes
    client_id: int
    server_id: int
    enabled: bool = True


@attr.s(auto_attribs=True)
class SapAssignment:
    """COSEM IC SAP Assignment (class_id=17).

    Attributes:
        1: logical_name (static)
        2: assignments (dynamic, array of SapAssignmentEntry)
        3: default_sap (dynamic, unsigned)
    Methods:
        1: add_assignment
        2: remove_assignment
        3: get_sap_for_context
        4: enable_assignment
        5: disable_assignment
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SAP_ASSIGNMENT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    assignments: List[SapAssignmentEntry] = attr.ib(factory=list)
    default_sap: int = 1

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="assignments"),
        3: AttributeDescription(attribute_id=3, attribute_name="default_sap"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "add_assignment",
        2: "remove_assignment",
        3: "get_sap_for_context",
        4: "enable_assignment",
        5: "disable_assignment",
    }

    def add_assignment(self, sap_id: int, app_context: bytes, client_id: int, server_id: int) -> None:
        """Method 1: Add a SAP assignment."""
        entry = SapAssignmentEntry(
            sap_id=sap_id,
            application_context=app_context,
            client_id=client_id,
            server_id=server_id,
            enabled=True,
        )
        self.assignments.append(entry)

    def remove_assignment(self, sap_id: int) -> bool:
        """Method 2: Remove a SAP assignment."""
        for i, entry in enumerate(self.assignments):
            if entry.sap_id == sap_id:
                self.assignments.pop(i)
                return True
        return False

    def get_sap_for_context(self, app_context: bytes) -> int:
        """Method 3: Get SAP ID for an application context."""
        for entry in self.assignments:
            if entry.application_context == app_context and entry.enabled:
                return entry.sap_id
        return self.default_sap

    def enable_assignment(self, sap_id: int) -> bool:
        """Method 4: Enable a SAP assignment."""
        for entry in self.assignments:
            if entry.sap_id == sap_id:
                entry.enabled = True
                return True
        return False

    def disable_assignment(self, sap_id: int) -> bool:
        """Method 5: Disable a SAP assignment."""
        for entry in self.assignments:
            if entry.sap_id == sap_id:
                entry.enabled = False
                return True
        return False

    def set_default_sap(self, sap_id: int) -> None:
        """Set the default SAP."""
        self.default_sap = sap_id

    def get_assignment_by_sap(self, sap_id: int) -> SapAssignmentEntry:
        """Get assignment by SAP ID."""
        for entry in self.assignments:
            if entry.sap_id == sap_id:
                return entry
        return None

    def is_assignment_enabled(self, sap_id: int) -> bool:
        """Check if a SAP assignment is enabled."""
        entry = self.get_assignment_by_sap(sap_id)
        return entry is not None and entry.enabled

    def get_enabled_assignment_count(self) -> int:
        """Get the number of enabled assignments."""
        return sum(1 for entry in self.assignments if entry.enabled)

    def clear_assignments(self) -> None:
        """Clear all assignments."""
        self.assignments = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
