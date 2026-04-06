"""IC class 21 - Register Monitor.

Monitors the value of a Register or Extended Register and compares it against
thresholds. Used for demand monitoring and limit checking.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ThresholdsValue:
    """A thresholds value entry containing thresholds list and actions."""
    thresholds: List[Any] = attr.ib(factory=list)
    actions: List[int] = attr.ib(factory=list)


@attr.s(auto_attribs=True)
class RegisterMonitor:
    """COSEM IC Register Monitor (class_id=21).

    Attributes:
        1: logical_name (static)
        2: thresholds (static)
        3: monitored_object (static, CosemAttribute)
        4: monitored_attribute (static)
        5: selected_object (static, CosemAttribute)
        6: selected_attribute (static)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.REGISTER_MONITOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    thresholds: List[ThresholdsValue] = attr.ib(factory=list)
    monitored_object: Optional[str] = None
    monitored_attribute: int = 2
    selected_object: Optional[str] = None
    selected_attribute: int = 2

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="thresholds"),
        3: AttributeDescription(attribute_id=3, attribute_name="monitored_object"),
        4: AttributeDescription(attribute_id=4, attribute_name="monitored_attribute"),
        5: AttributeDescription(attribute_id=5, attribute_name="selected_object"),
        6: AttributeDescription(attribute_id=6, attribute_name="selected_attribute"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset the register monitor."""
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
