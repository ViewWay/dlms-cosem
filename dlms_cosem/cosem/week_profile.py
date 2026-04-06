"""Week Profile.

Maps each day of the week to a day profile ID.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class WeekProfileEntry:
    """Maps week_number to day profile IDs for Mon-Sun."""
    week_name: str
    monday: int = 1
    tuesday: int = 1
    wednesday: int = 1
    thursday: int = 1
    friday: int = 1
    saturday: int = 1
    sunday: int = 1


@attr.s(auto_attribs=True)
class WeekProfile:
    """Week Profile definition.

    Attributes:
        1: logical_name (static)
        2: week_profile (static) - list of WeekProfileEntry
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.UTILITY_TABLES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    week_profile: List[WeekProfileEntry] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="week_profile"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
