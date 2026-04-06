"""IC class 68 - Arbitrator.

Arbitrator for managing multiple clients accessing same resource.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.11
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Arbitrator:
    """COSEM IC Arbitrator (class_id=68).

    Attributes:
        1: logical_name (static)
        2: controls (dynamic) - List of controls
        3: permissions (dynamic) - Permission settings
        4: arbitration_table (dynamic) - Table of arbitration rules
        5: active_controls (dynamic) - Currently active controls
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ARBITRATOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    controls: List[Dict[str, Any]] = attr.ib(factory=list)
    permissions: List[int] = attr.ib(factory=list)
    arbitration_table: List[Dict[str, Any]] = attr.ib(factory=list)
    active_controls: List[int] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="controls"),
        3: AttributeDescription(attribute_id=3, attribute_name="permissions"),
        4: AttributeDescription(attribute_id=4, attribute_name="arbitration_table"),
        5: AttributeDescription(attribute_id=5, attribute_name="active_controls"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset arbitrator."""
        self.active_controls = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def activate_control(self, control_id: int) -> None:
        """Activate a control."""
        if control_id not in self.active_controls:
            self.active_controls.append(control_id)

    def deactivate_control(self, control_id: int) -> None:
        """Deactivate a control."""
        if control_id in self.active_controls:
            self.active_controls.remove(control_id)
