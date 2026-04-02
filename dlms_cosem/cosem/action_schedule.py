"""IC class 10 - Schedule (Action Schedule).

Defines multiple time-bound actions, grouped by day profiles. Used for
complex tariff switching, load control, etc.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ActionSchedule:
    """COSEM IC Action Schedule (class_id=10).

    Attributes:
        1: logical_name (static)
        2: activate_passive_time (static, CosemDateTime)
        3: action_schedule (static) - list of (season_profile_name, week_profile)
        4: executions (dynamic) - list of scheduled executions
    Methods:
        1: add_entry
        2: remove_entry
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SCHEDULE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    activate_passive_time: Optional[bytes] = None
    action_schedule: List[Any] = attr.ib(factory=list)
    executions: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="activate_passive_time"),
        3: AttributeDescription(attribute_id=3, attribute_name="action_schedule"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        4: AttributeDescription(attribute_id=4, attribute_name="executions"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "add_entry", 2: "remove_entry"}

    def add_entry(self, entry: Any) -> None:
        self.action_schedule.append(entry)

    def remove_entry(self, index: int) -> None:
        if 0 <= index < len(self.action_schedule):
            self.action_schedule.pop(index)

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
