"""IC class 8 - Clock.

Provides date and time functionality. Critical for tariff switching,
demand calculation, and event logging.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.8
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Clock:
    """COSEM IC Clock (class_id=8).

    Attributes:
        1: logical_name (static)
        2: time (dynamic, CosemDateTime)
        3: time_zone (static, signed short, minutes)
        4: status (dynamic, bitstring)
        5: daylight_savings_begin (static, CosemDateTime)
        6: daylight_savings_end (static, CosemDateTime)
        7: daylight_savings_deviation (static, signed short)
        8: daylight_savings_enabled (static, boolean)
        9: clock_base (static, enum)
    Methods:
        1: adjust_time
        2: adjust_to_quarter
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CLOCK
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    time: Optional[datetime] = None
    time_zone: int = 480  # UTC+8 for China (minutes)
    status: int = 0
    daylight_savings_begin: Optional[datetime] = None
    daylight_savings_end: Optional[datetime] = None
    daylight_savings_deviation: int = 60
    daylight_savings_enabled: bool = False
    clock_base: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="time_zone"),
        5: AttributeDescription(attribute_id=5, attribute_name="daylight_savings_begin"),
        6: AttributeDescription(attribute_id=6, attribute_name="daylight_savings_end"),
        7: AttributeDescription(attribute_id=7, attribute_name="daylight_savings_deviation"),
        8: AttributeDescription(attribute_id=8, attribute_name="daylight_savings_enabled"),
        9: AttributeDescription(attribute_id=9, attribute_name="clock_base"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="time"),
        4: AttributeDescription(attribute_id=4, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "adjust_time", 2: "adjust_to_quarter"}

    def adjust_time(self, delta_minutes: int) -> None:
        if self.time and delta_minutes != 0:
            from datetime import timedelta
            self.time += timedelta(minutes=delta_minutes)

    def adjust_to_quarter(self) -> None:
        """Adjust time to nearest quarter hour."""
        if self.time:
            m = self.time.minute
            if m < 8:
                adj = -m
            elif m < 23:
                adj = 15 - m
            elif m < 38:
                adj = 30 - m
            elif m < 53:
                adj = 45 - m
            else:
                adj = 60 - m
            self.adjust_time(adj)

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
