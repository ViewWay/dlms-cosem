"""IC class 110 - M-Bus Diagnostic.

Diagnostic information for M-Bus communication.
Used in wired and wireless M-Bus metering systems.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.110
"""
from typing import ClassVar, Dict

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class MbusDiagnostic:
    """COSEM IC M-Bus Diagnostic (class_id=110).

    Attributes:
        1: logical_name (static)
        2: total_messages_sent (dynamic, double-long-unsigned)
        3: total_messages_received (dynamic, double-long-unsigned)
        4: failed_messages (dynamic, double-long-unsigned)
        5: crc_errors (dynamic, double-long-unsigned)
        6: timeout_errors (dynamic, double-long-unsigned)
        7: last_error_code (dynamic, unsigned)
        8: signal_quality (dynamic, unsigned)
        9: bus_voltage (dynamic, float)
    Methods:
        1: reset_counters
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_DIAGNOSTIC
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    total_messages_sent: int = 0
    total_messages_received: int = 0
    failed_messages: int = 0
    crc_errors: int = 0
    timeout_errors: int = 0
    last_error_code: int = 0
    signal_quality: int = 0
    bus_voltage: float = 0.0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="total_messages_sent"),
        3: AttributeDescription(attribute_id=3, attribute_name="total_messages_received"),
        4: AttributeDescription(attribute_id=4, attribute_name="failed_messages"),
        5: AttributeDescription(attribute_id=5, attribute_name="crc_errors"),
        6: AttributeDescription(attribute_id=6, attribute_name="timeout_errors"),
        7: AttributeDescription(attribute_id=7, attribute_name="last_error_code"),
        8: AttributeDescription(attribute_id=8, attribute_name="signal_quality"),
        9: AttributeDescription(attribute_id=9, attribute_name="bus_voltage"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset_counters"}

    def increment_sent(self) -> None:
        """Increment sent message counter."""
        self.total_messages_sent += 1

    def increment_received(self) -> None:
        """Increment received message counter."""
        self.total_messages_received += 1

    def increment_failed(self) -> None:
        """Increment failed message counter."""
        self.failed_messages += 1

    def increment_crc_error(self) -> None:
        """Increment CRC error counter."""
        self.crc_errors += 1

    def increment_timeout_error(self) -> None:
        """Increment timeout error counter."""
        self.timeout_errors += 1

    def set_last_error_code(self, code: int) -> None:
        """Set the last error code."""
        self.last_error_code = code

    def set_signal_quality(self, quality: int) -> None:
        """Set signal quality (0-100)."""
        self.signal_quality = max(0, min(100, quality))

    def set_bus_voltage(self, voltage: float) -> None:
        """Set bus voltage in volts."""
        self.bus_voltage = voltage

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.total_messages_sent + self.total_messages_received
        if total == 0:
            return 100.0
        failed = self.failed_messages
        return (1.0 - failed / total) * 100.0

    def get_total_errors(self) -> int:
        """Get total error count."""
        return self.failed_messages + self.crc_errors + self.timeout_errors

    def reset_counters(self) -> None:
        """Method 1: Reset all diagnostic counters."""
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.failed_messages = 0
        self.crc_errors = 0
        self.timeout_errors = 0
        self.last_error_code = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
