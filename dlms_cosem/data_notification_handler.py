"""
Data Notification Handler for DLMS/COSEM.

This module provides utilities for handling data notifications pushed from meters.
Data notifications are unsolicited messages sent by meters to push data without
requiring a poll/request from the client.

Common use cases:
- Smart meters pushing consumption data
- Event notifications (alarm, status changes)
- Profile buffer updates
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from enum import IntEnum

from dlms_cosem import utils
from dlms_cosem.protocol.xdlms.data_notification import DataNotification


class NotificationEventType(IntEnum):
    """Types of notification events."""
    DATA_UPDATE = 1
    ALARM = 2
    EVENT = 3
    STATUS_CHANGE = 4
    PROFILE_UPDATE = 5


@dataclass
class NotificationEvent:
    """
    A data notification event from a meter.

    Attributes:
        event_type: Type of notification
        source_address: Logical address of the sending meter
        date_time: Timestamp of the notification (optional)
        data: Raw notification data
        parsed_data: Parsed DLMS data (if available)
    """
    event_type: NotificationEventType
    source_address: Optional[int]
    date_time: Optional[Any]
    data: bytes
    parsed_data: Optional[Any] = None

    def __repr__(self) -> str:
        return (
            f"NotificationEvent(type={self.event_type.name}, "
            f"source={self.source_address}, "
            f"data_len={len(self.data)})"
        )


class DataNotificationHandler:
    """
    Handler for DLMS/COSEM data notifications.

    This handler processes incoming data notifications and dispatches them
    to registered callbacks based on event type or source address.

    Example:
        >>> handler = DataNotificationHandler()
        >>>
        >>> # Register a callback for all notifications
        >>> @handler.on_any
        >>> def handle_all(event):
        ...     print(f"Received: {event}")
        >>>
        >>> # Register a callback for specific source
        >>> @handler.on_source(1)
        >>> def handle_meter_1(event):
        ...     print(f"Meter 1: {event}")
        >>>
        >>> # Process a notification
        >>> handler.handle(b'\\x0f\\x00\\x00\\x01...')
    """

    def __init__(self):
        self._global_callbacks: List[Callable[[NotificationEvent], None]] = []
        self._type_callbacks: Dict[NotificationEventType, List[Callable]] = {}
        self._source_callbacks: Dict[int, List[Callable]] = {}

    def on_any(self, callback: Callable[[NotificationEvent], None]):
        """Register a callback for all notifications."""
        self._global_callbacks.append(callback)
        return callback

    def on_type(
        self, event_type: NotificationEventType
    ) -> Callable[[Callable[[NotificationEvent], None]], None]:
        """Register a callback for specific event type."""
        def decorator(callback: Callable[[NotificationEvent], None]):
            if event_type not in self._type_callbacks:
                self._type_callbacks[event_type] = []
            self._type_callbacks[event_type].append(callback)
            return callback
        return decorator

    def on_source(
        self, source_address: int
    ) -> Callable[[Callable[[NotificationEvent], None]], None]:
        """Register a callback for specific source meter."""
        def decorator(callback: Callable[[NotificationEvent], None]):
            if source_address not in self._source_callbacks:
                self._source_callbacks[source_address] = []
            self._source_callbacks[source_address].append(callback)
            return callback
        return decorator

    def handle(self, data: bytes, source_address: Optional[int] = None) -> NotificationEvent:
        """
        Handle a raw data notification.

        Args:
            data: Raw data notification bytes
            source_address: Logical address of the source meter

        Returns:
            NotificationEvent with parsed data
        """
        # Parse the data notification
        notification = DataNotification.from_bytes(data)

        # Parse the body as DLMS data
        parsed_data = None
        try:
            parsed_data = utils.parse_as_dlms_data(notification.body)
        except Exception:
            pass  # Keep parsed_data as None if parsing fails

        # Create event
        event = NotificationEvent(
            event_type=self._detect_event_type(parsed_data),
            source_address=source_address,
            date_time=notification.date_time,
            data=notification.body,
            parsed_data=parsed_data,
        )

        # Dispatch to callbacks
        self._dispatch(event)

        return event

    def _detect_event_type(self, parsed_data: Any) -> NotificationEventType:
        """Detect event type from parsed data."""
        # Default to data update
        event_type = NotificationEventType.DATA_UPDATE

        if parsed_data:
            # You can add more sophisticated detection here
            # For example, checking for specific OBIS codes or values
            if hasattr(parsed_data, '__iter__') and not isinstance(parsed_data, (bytes, str)):
                # Check for alarm/event indicators in the data
                pass

        return event_type

    def _dispatch(self, event: NotificationEvent) -> None:
        """Dispatch event to registered callbacks."""
        # Global callbacks
        for callback in self._global_callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Continue even if callback fails

        # Type-specific callbacks
        for callback in self._type_callbacks.get(event.event_type, []):
            try:
                callback(event)
            except Exception:
                pass

        # Source-specific callbacks
        if event.source_address:
            for callback in self._source_callbacks.get(event.source_address, []):
                try:
                    callback(event)
                except Exception:
                    pass

    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self._global_callbacks.clear()
        self._type_callbacks.clear()
        self._source_callbacks.clear()


class DataNotificationBuffer:
    """
    Buffer for storing data notifications.

    Useful for collecting notifications over time for batch processing
    or for notifications that arrive out of order.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the notification buffer.

        Args:
            max_size: Maximum number of notifications to store
        """
        self.max_size = max_size
        self._notifications: List[NotificationEvent] = []

    def add(self, notification: NotificationEvent) -> None:
        """
        Add a notification to the buffer.

        If the buffer is full, oldest notifications are removed.
        """
        self._notifications.append(notification)
        if len(self._notifications) > self.max_size:
            self._notifications = self._notifications[-self.max_size:]

    def get_all(self) -> List[NotificationEvent]:
        """Get all notifications in the buffer."""
        return self._notifications.copy()

    def get_by_source(self, source_address: int) -> List[NotificationEvent]:
        """Get notifications from a specific source."""
        return [
            n for n in self._notifications
            if n.source_address == source_address
        ]

    def get_by_type(self, event_type: NotificationEventType) -> List[NotificationEvent]:
        """Get notifications of a specific type."""
        return [
            n for n in self._notifications
            if n.event_type == event_type
        ]

    def clear(self) -> None:
        """Clear all notifications from the buffer."""
        self._notifications.clear()

    def __len__(self) -> int:
        return len(self._notifications)
