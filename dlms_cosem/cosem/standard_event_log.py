"""IC027 - Standard Event Log.

Standardized event logging per DLMS/COSEM Blue Book specification.
Predefined event codes for common meter events (power outages,
tamper, clock adjustments, etc.).

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


class StandardEventCode:
    """Predefined standard event codes per Blue Book."""
    VOLTAGE_BELOW_THRESHOLD = 1
    VOLTAGE_ABOVE_THRESHOLD = 2
    CURRENT_BELOW_THRESHOLD = 3
    CURRENT_ABOVE_THRESHOLD = 4
    POWER_FAILURE = 5
    POWER_RESTORED = 6
    TARIFF_CHANGED = 7
    CLOCK_ADJUSTED = 8
    METER_COVER_OPENED = 9
    METER_COVER_CLOSED = 10
    BATTERY_LOW = 11
    BATTERY_REPLACED = 12
    PROGRAMMING_CHANGED = 13
    MAX_DEMAND_RESET = 14
    TEST_MODE = 15
    TARIFF_ACTIVATION = 16
    DATA_VALIDATION_FAILED = 17
    MEMORY_ERROR = 18
    WATCHDOG_RESET = 19
    FIRMWARE_UPDATE = 20


@attr.s(auto_attribs=True)
class StandardEventLogEntry:
    """A standard event log entry."""
    event_code: int
    timestamp: Optional[datetime] = None
    event_data: Optional[Any] = None

    @property
    def event_name(self) -> str:
        for name, code in vars(StandardEventCode).items():
            if code == self.event_code:
                return name
        return f"UNKNOWN_EVENT_{self.event_code}"


@attr.s(auto_attribs=True)
class StandardEventLog:
    """COSEM IC Standard Event Log (class_id=27).

    Attributes:
        1: logical_name (static)
        2: buffer (dynamic)
        3: capture_objects (static)
        4: event_filter (static, bitmask of enabled events)
    Methods:
        1: reset
        2: add_event
    """

    CLASS_ID: ClassVar[int] = 27
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    entries: List[StandardEventLogEntry] = attr.ib(factory=list)
    capture_objects: list = attr.ib(factory=list)
    event_filter: int = 0xFFFFFFFF  # all events enabled by default
    max_entries: int = 100

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_objects"),
        4: AttributeDescription(attribute_id=4, attribute_name="event_filter"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="buffer"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "add_event"}

    def add_event(self, event_code: int, timestamp: Optional[datetime] = None,
                  event_data: Any = None) -> None:
        if not (self.event_filter & (1 << (event_code - 1))):
            return  # event filtered out
        if timestamp is None:
            timestamp = datetime.now()
        self.entries.append(StandardEventLogEntry(
            event_code=event_code, timestamp=timestamp, event_data=event_data,
        ))
        # Trim to max_entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_events(self, event_code: Optional[int] = None,
                   since: Optional[datetime] = None) -> List[StandardEventLogEntry]:
        result = self.entries
        if event_code is not None:
            result = [e for e in result if e.event_code == event_code]
        if since is not None:
            result = [e for e in result if e.timestamp and e.timestamp >= since]
        return result

    def reset(self) -> None:
        self.entries = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
