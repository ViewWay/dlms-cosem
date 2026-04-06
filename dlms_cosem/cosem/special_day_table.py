"""IC class 11 - Special Day Table.

Defines special days (holidays) that override normal day profiles.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class SpecialDayEntry:
    """A special day entry: (day_index, date, day_profile_id)."""
    day_index: int = 0
    date: Optional[bytes] = None  # CosemDate
    day_profile_id: int = 255


@attr.s(auto_attribs=True)
class SpecialDayTable:
    """COSEM IC Special Day Table (class_id=11).

    Attributes:
        1: logical_name (static)
        2: special_day_table (static) - list of SpecialDayEntry
    Methods:
        1: add_entry
        2: remove_entry
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SPECIAL_DAYS_TABLE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    special_day_table: List[SpecialDayEntry] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="special_day_table"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "add_entry", 2: "remove_entry"}

    def add_entry(self, entry: SpecialDayEntry) -> None:
        self.special_day_table.append(entry)

    def remove_entry(self, day_index: int) -> None:
        self.special_day_table = [
            e for e in self.special_day_table if e.day_index != day_index
        ]

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
