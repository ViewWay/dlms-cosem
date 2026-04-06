"""Day Profile.

Defines time segments within a day, each mapped to a tariff/action schedule.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class DayProfileEntry:
    """A time segment within a day."""
    start_time: str  # HH:MM
    tariff_index: int = 1
    script_logical_name: Optional[str] = None


@attr.s(auto_attribs=True)
class DayProfile:
    """Day Profile definition.

    Attributes:
        1: logical_name (static)
        2: day_profile (static) - list of DayProfileEntry
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.UTILITY_TABLES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    day_profile: List[DayProfileEntry] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="day_profile"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
