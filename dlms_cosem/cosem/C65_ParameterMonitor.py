"""IC class 65 - Parameter Monitor.

Parameter monitoring and change tracking.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.6
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ParameterMonitor:
    """COSEM IC Parameter Monitor (class_id=65).

    Attributes:
        1: logical_name (static)
        2: parameter_list (dynamic) - List of parameters to monitor
        3: parameter_value (dynamic) - Current parameter values
        4: capture_time (dynamic) - Time of last capture
        5: changed_parameter (dynamic) - Which parameter changed
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PARAMETER_MONITOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    parameter_list: List[Dict[str, Any]] = attr.ib(factory=list)
    parameter_value: List[Any] = attr.ib(factory=list)
    capture_time: Optional[bytes] = None
    changed_parameter: Optional[Dict[str, Any]] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="parameter_list"),
        3: AttributeDescription(attribute_id=3, attribute_name="parameter_value"),
        4: AttributeDescription(attribute_id=4, attribute_name="capture_time"),
        5: AttributeDescription(attribute_id=5, attribute_name="changed_parameter"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset parameter monitor."""
        self.parameter_value = []
        self.capture_time = None
        self.changed_parameter = None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def add_parameter(self, class_id: int, obis: Obis, attribute_id: int) -> None:
        """Add a parameter to monitor."""
        self.parameter_list.append({
            "class_id": class_id,
            "logical_name": obis,
            "attribute_id": attribute_id,
        })
