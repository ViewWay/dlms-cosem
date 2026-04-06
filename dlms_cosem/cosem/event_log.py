"""Event Log - Standard event logging.

Stores meter events (power outages, tamper attempts, meter resets, etc.)
in a Profile Generic buffer.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class EventLogEntry:
    """A single event log entry."""
    event_code: int
    timestamp: Optional[datetime] = None
    event_data: Optional[Any] = None


@attr.s(auto_attribs=True)
class EventLog:
    """COSEM IC Event Log (class_id=7, Profile Generic based).

    Attributes:
        1: logical_name (static)
        2: buffer (dynamic) - list of event entries
        3: capture_objects (static)
        4: log_name (static) - descriptive name
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PROFILE_GENERIC
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    entries: List[EventLogEntry] = attr.ib(factory=list)
    capture_objects: list = attr.ib(factory=list)
    log_name: str = "Standard Event Log"

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_objects"),
        4: AttributeDescription(attribute_id=4, attribute_name="log_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="buffer"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def add_event(self, event_code: int, timestamp: Optional[datetime] = None,
                  event_data: Any = None) -> None:
        if timestamp is None:
            timestamp = datetime.now()
        self.entries.append(EventLogEntry(
            event_code=event_code,
            timestamp=timestamp,
            event_data=event_data,
        ))

    def reset(self) -> None:
        self.entries = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
