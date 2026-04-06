"""IC029 - Event Notification.

Pushes event notifications from the meter to the client (data notification).
Used for real-time alarm/event reporting.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class EventNotification:
    """COSEM IC Event Notification (class_id=29).

    Manages event notifications pushed from the meter.

    Attributes:
        1: logical_name (static)
        2: notification_type (static, enum)
        3: event_list (static, list of event codes to notify)
        4: enabled (dynamic, boolean)
        5: notification_count (dynamic)
        6: last_notification_time (dynamic)
    Methods:
        1: enable
        2: disable
        3: send_notification
    """

    CLASS_ID: ClassVar[int] = 29
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    notification_type: int = 0  # 0=immediate, 1=deferred
    event_list: List[int] = attr.ib(factory=list)
    enabled: bool = False
    notification_count: int = 0
    last_notification_time: Optional[datetime] = None
    pending_notifications: List[Dict[str, Any]] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="notification_type"),
        3: AttributeDescription(attribute_id=3, attribute_name="event_list"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        4: AttributeDescription(attribute_id=4, attribute_name="enabled"),
        5: AttributeDescription(attribute_id=5, attribute_name="notification_count"),
        6: AttributeDescription(attribute_id=6, attribute_name="last_notification_time"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "enable", 2: "disable", 3: "send_notification"
    }

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def notify(self, event_code: int, event_data: Any = None) -> Optional[Dict]:
        if not self.enabled:
            return None
        if self.event_list and event_code not in self.event_list:
            return None
        notification = {
            "event_code": event_code,
            "timestamp": datetime.now(),
            "event_data": event_data,
        }
        self.notification_count += 1
        self.last_notification_time = notification["timestamp"]
        self.pending_notifications.append(notification)
        return notification

    def get_pending(self) -> List[Dict]:
        pending = self.pending_notifications[:]
        self.pending_notifications = []
        return pending

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
