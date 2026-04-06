"""IC class 22 - Single Action Schedule.

Executes a single script at a specified time. Used for time-bound actions
like rate changes or data capture.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class SingleActionSchedule:
    """COSEM IC Single Action Schedule (class_id=22).

    Attributes:
        1: logical_name (static)
        2: executed_script (static, CosemMethod)
        3: type (static) - 0=once, 1=periodic
        4: execution_time (static, octet-string datetime)
    Methods:
        1: execute
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SINGLE_ACTION_SCHEDULE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    executed_script: Optional[str] = None
    schedule_type: int = 0
    execution_time: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="executed_script"),
        3: AttributeDescription(attribute_id=3, attribute_name="type"),
        4: AttributeDescription(attribute_id=4, attribute_name="execution_time"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "execute"}

    def execute(self) -> None:
        """Method 1: Execute the scheduled script."""
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
