"""IC028 - Utility Event Log.

Utility-specific (custom) event logging. Allows utilities to define
their own event codes beyond the standard set.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class UtilityEventLogEntry:
    """A utility-specific event log entry."""
    event_code: int
    timestamp: Optional[datetime] = None
    event_data: Optional[Any] = None
    event_description: str = ""


@attr.s(auto_attribs=True)
class UtilityEventLog:
    """COSEM IC Utility Event Log (class_id=28).

    Attributes:
        1: logical_name (static)
        2: buffer (dynamic)
        3: capture_objects (static)
        4: event_filter (static, bitmask)
        5: event_code_map (static, mapping code->description)
    Methods:
        1: reset
        2: add_event
    """

    CLASS_ID: ClassVar[int] = 28
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    entries: List[UtilityEventLogEntry] = attr.ib(factory=list)
    capture_objects: list = attr.ib(factory=list)
    event_filter: int = 0xFFFFFFFF
    event_code_map: Dict[int, str] = attr.ib(factory=dict)
    max_entries: int = 200

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_objects"),
        4: AttributeDescription(attribute_id=4, attribute_name="event_filter"),
        5: AttributeDescription(attribute_id=5, attribute_name="event_code_map"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="buffer"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "add_event"}

    def register_event_code(self, code: int, description: str) -> None:
        self.event_code_map[code] = description

    def add_event(self, event_code: int, timestamp: Optional[datetime] = None,
                  event_data: Any = None) -> None:
        if not (self.event_filter & (1 << (event_code - 1))):
            return
        if timestamp is None:
            timestamp = datetime.now()
        desc = self.event_code_map.get(event_code, "")
        self.entries.append(UtilityEventLogEntry(
            event_code=event_code, timestamp=timestamp,
            event_data=event_data, event_description=desc,
        ))
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_events(self, event_code: Optional[int] = None,
                   since: Optional[datetime] = None) -> List[UtilityEventLogEntry]:
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
