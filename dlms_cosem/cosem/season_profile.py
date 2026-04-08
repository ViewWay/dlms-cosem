"""Season Profile.

Defines the start/end dates of seasons, mapping each season to a week profile.
Used in Activity Calendar and Schedule objects.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class SeasonProfileEntry:
    """A single season entry: (season_name, start, week_profile_name)."""
    season_name: str
    start: Optional[bytes] = None  # CosemDateTime
    week_profile_name: str = ""


@attr.s(auto_attribs=True)
class SeasonProfile:
    """Season Profile definition.

    Attributes:
        1: logical_name (static)
        2: season_profile (static) - list of SeasonProfileEntry
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.UTILITY_TABLES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    season_profile: List[SeasonProfileEntry] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="season_profile"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
