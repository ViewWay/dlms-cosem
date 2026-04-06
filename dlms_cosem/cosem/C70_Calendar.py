"""IC class 70 - Calendar.

Calendar management for scheduling and time-based operations.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: calendar_name_active (static)
    3: season_profile_active (static)
    4: week_profile_active (static)
    5: day_profile_active (static)
    6: calendar_name_passive (static)
    7: season_profile_passive (static)
    8: week_profile_passive (static)
    9: day_profile_passive (static)
    10: time_zone (static)
    11: season_time_offset (static)
    12: week_start (static)
"""
from typing import ClassVar, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SeasonEntry:
    """Season entry for calendar."""
    season_name: str = ""
    start_date: Optional[bytes] = None
    end_date: Optional[bytes] = None


@attr.s(auto_attribs=True)
class WeekDayProfile:
    """Week day profile entry."""
    day_id: int = 0
    day_schedule_id: int = 0


@attr.s(auto_attribs=True)
class Calendar:
    """COSEM IC Calendar (class_id=70).

    Attributes:
        1: logical_name (static)
        2: calendar_name_active (static)
        3: season_profile_active (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CALENDAR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    calendar_name_active: str = ""
    seasons: List[SeasonEntry] = attr.ib(factory=list)
    week_profiles: List[WeekDayProfile] = attr.ib(factory=list)
    time_zone: int = 0
