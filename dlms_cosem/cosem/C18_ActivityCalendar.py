"""IC class 20 - Activity Calendar.

Defines activity periods and special days for tariff calculation.
Used in complex tariff schemes with calendar-based rates.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.20
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ActivityPeriod:
    """An activity period in the calendar."""
    start_date: str  # Format: MM-DD
    end_date: str    # Format: MM-DD
    activity_id: int
    description: str


@attr.s(auto_attribs=True)
class ActivityCalendar:
    """COSEM IC Activity Calendar (class_id=20).

    Attributes:
        1: logical_name (static)
        2: activity_periods (dynamic, array of ActivityPeriod)
        3: calendar_name (dynamic, visible-string)
    Methods:
        1: add_period
        2: remove_period
        3: get_activity_for_date
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ACTIVITY_CALENDAR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    activity_periods: List[ActivityPeriod] = attr.ib(factory=list)
    calendar_name: str = ""

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="activity_periods"),
        3: AttributeDescription(attribute_id=3, attribute_name="calendar_name"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "add_period", 2: "remove_period", 3: "get_activity_for_date"}

    def add_period(self, start_date: str, end_date: str, activity_id: int, description: str = "") -> None:
        """Method 1: Add an activity period."""
        period = ActivityPeriod(
            start_date=start_date,
            end_date=end_date,
            activity_id=activity_id,
            description=description,
        )
        self.activity_periods.append(period)

    def remove_period(self, activity_id: int) -> bool:
        """Method 2: Remove an activity period by activity ID."""
        for i, period in enumerate(self.activity_periods):
            if period.activity_id == activity_id:
                self.activity_periods.pop(i)
                return True
        return False

    def get_activity_for_date(self, date_str: str) -> int:
        """Method 3: Get activity ID for a given date (format: MM-DD)."""
        for period in self.activity_periods:
            # Simple string comparison for date ranges
            if period.start_date <= date_str <= period.end_date:
                return period.activity_id
        return 0  # Default activity

    def set_calendar_name(self, name: str) -> None:
        """Set the calendar name."""
        self.calendar_name = name

    def get_period_count(self) -> int:
        """Get the number of activity periods."""
        return len(self.activity_periods)

    def get_period_by_activity_id(self, activity_id: int) -> ActivityPeriod:
        """Get period by activity ID."""
        for period in self.activity_periods:
            if period.activity_id == activity_id:
                return period
        return None

    def clear_periods(self) -> None:
        """Clear all activity periods."""
        self.activity_periods = []

    def is_date_in_period(self, date_str: str, activity_id: int) -> bool:
        """Check if a date is in a specific activity period."""
        period = self.get_period_by_activity_id(activity_id)
        if period is None:
            return False
        return period.start_date <= date_str <= period.end_date

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
