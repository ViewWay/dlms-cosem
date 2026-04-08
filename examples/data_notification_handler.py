#!/usr/bin/env python3
"""
Data Notification Handler Example

This example demonstrates how to use the DataNotificationHandler
to process unsolicited data pushed from DLMS/COSEM meters.

Data notifications are commonly used for:
- Smart meters pushing consumption data at regular intervals
- Event notifications (alarms, status changes)
- Profile buffer updates
"""
from dlms_cosem.data_notification_handler import (
    DataNotificationHandler,
    DataNotificationBuffer,
    NotificationEventType,
    NotificationEvent,
)


def example_basic_handler():
    """
    Example 1: Basic notification handling.
    """
    print("=== Example 1: Basic Notification Handling ===\n")

    handler = DataNotificationHandler()

    # Register a callback for all notifications
    @handler.on_any
    def handle_all_notifications(event: NotificationEvent):
        print(f"Received notification from meter {event.source_address}")
        print(f"  Type: {event.event_type.name}")
        print(f"  Data length: {len(event.data)} bytes")
        if event.date_time:
            print(f"  Timestamp: {event.date_time}")
        print()

    # Simulate receiving a notification
    sample_notification = b'\x0f\x00\x00\x01\xdb\x00\t"\x12Z\x85\x916\x00\x00\x00\x00I\x00\x00\x00\x11\x00\x00\x00\nZ\x85\x13\xd0\x14\x80\x00\x00\x00\r\x00\x00\x00\n\x01\x00'

    print("Processing sample notification...")
    handler.handle(sample_notification, source_address=1)


def example_filtered_handlers():
    """
    Example 2: Filtered handlers by event type and source.
    """
    print("=== Example 2: Filtered Handlers ===\n")

    handler = DataNotificationHandler()

    # Handler for data updates only
    @handler.on_type(NotificationEventType.DATA_UPDATE)
    def handle_data_update(event: NotificationEvent):
        print(f"[DATA UPDATE] Source: {event.source_address}")

    # Handler for alarms only
    @handler.on_type(NotificationEventType.ALARM)
    def handle_alarm(event: NotificationEvent):
        print(f"[ALARM] Source: {event.source_address} - Check meter!")

    # Handler for specific meter
    @handler.on_source(1)
    def handle_meter_1(event: NotificationEvent):
        print(f"[METER 1] Processing: {event.event_type.name}")

    # Simulate notifications from different sources
    sample_data = b'\x0f\x00\x00\x01\xdb\x00\t"\x12Z\x85\x916\x00\x00\x00\x00I\x00\x00\x00\x11\x00\x00\x00\nZ\x85\x13\xd0\x14\x80\x00\x00\x00\r\x00\x00\x00\n\x01\x00'

    print("Processing notifications from different meters...")
    handler.handle(sample_data, source_address=1)
    handler.handle(sample_data, source_address=2)
    print()


def example_buffered_notifications():
    """
    Example 3: Buffering notifications for batch processing.
    """
    print("=== Example 3: Buffered Notifications ===\n")

    buffer = DataNotificationBuffer(max_size=100)

    # Create a handler that adds notifications to buffer
    handler = DataNotificationHandler()

    @handler.on_any
    def buffer_notifications(event: NotificationEvent):
        buffer.add(event)
        print(f"Buffered notification from meter {event.source_address}")
        print(f"  Buffer size: {len(buffer)}")

    # Process multiple notifications
    sample_data = b'\x0f\x00\x00\x01\xdb\x00\t"\x12Z\x85\x916\x00\x00\x00\x00I\x00\x00\x00\x11\x00\x00\x00\nZ\x85\x13\xd0\x14\x80\x00\x00\x00\r\x00\x00\x00\n\x01\x00'

    print("Processing multiple notifications...")
    for i in range(3):
        handler.handle(sample_data, source_address=1)

    print()

    # Retrieve notifications from buffer
    print(f"Total buffered notifications: {len(buffer)}")
    print(f"Notifications from meter 1: {len(buffer.get_by_source(1))}")
    print()


def example_integration_with_client():
    """
    Example 4: Integration with DlmsClient for real-time monitoring.

    This shows how you might integrate the handler with a real client
    to receive and process push notifications from meters.
    """
    print("=== Example 4: Integration Example ===\n")

    print("""
# Example: Integrating with a listening client
from dlms_cosem.client import DlmsClient
from dlms_cosem.data_notification_handler import DataNotificationHandler

# Create handler
handler = DataNotificationHandler()

@handler.on_type(NotificationEventType.ALARM)
def handle_alarms(event):
    # Send alert, log to database, etc.
    print(f"ALARM from meter {event.source_address}")
    notify_administrators(event)

# In a real scenario, you would:
# 1. Set up a listening socket/server
# 2. Parse incoming HDLC frames
# 3. Extract data notifications
# 4. Pass them to the handler

# Pseudo-code:
# server = DlmsServer(listen_port=4059)
# server.on_data_notification(lambda data: handler.handle(data))
# server.start()
""")


def example_custom_event_detection():
    """
    Example 5: Custom event type detection.

    You can extend the handler to detect specific event types
    based on the notification content (e.g., specific OBIS codes).
    """
    print("=== Example 5: Custom Event Detection ===\n")

    print("""
# Example: Custom handler with OBIS-based detection
from dlms_cosem.data_notification_handler import DataNotificationHandler

class SmartMeterNotificationHandler(DataNotificationHandler):
    def _detect_event_type(self, parsed_data):
        # Detect event type based on OBIS codes or values
        if parsed_data:
            # Check for alarm OBIS codes (usually 0.0.99.x.x.x)
            # Check for profile updates (usually 1.0.99.1.x.x)
            # Check for specific status values
            pass
        return super()._detect_event_type(parsed_data)

# Use the custom handler
handler = SmartMeterNotificationHandler()

@handler.on_type(NotificationEventType.ALARM)
def handle_alarm(event):
    # Handle alarm-specific logic
    pass
""")


if __name__ == "__main__":
    example_basic_handler()
    example_filtered_handlers()
    example_buffered_notifications()
    example_integration_with_client()
    example_custom_event_detection()

    print("\n=== Key Takeaways ===")
    print("1. DataNotificationHandler processes push notifications from meters")
    print("2. Use decorators to register callbacks for different event types")
    print("3. Filter by event type or source address")
    print("4. Buffer notifications for batch processing")
    print("5. Extend handler class for custom event detection")
