"""IC class 202 - Sag Swell Monitor.

Monitors voltage sags (dips) and swells (surges).
Used in power quality compliance monitoring (EN 50160, IEEE 1159).

Custom IC class for voltage quality monitoring.
"""
from typing import ClassVar, Dict

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class SagSwellMonitor:
    """COSEM IC Sag Swell Monitor (class_id=202).

    Attributes:
        1: logical_name (static)
        2: sag_threshold_percent (dynamic, unsigned)
        3: swell_threshold_percent (dynamic, unsigned)
        4: sag_count (dynamic, double-long-unsigned)
        5: swell_count (dynamic, double-long-unsigned)
        6: sag_duration_ms (dynamic, double-long-unsigned)
        7: swell_duration_ms (dynamic, double-long-unsigned)
        8: last_sag_depth_percent (dynamic, unsigned)
        9: last_swell_magnitude_percent (dynamic, unsigned)
        10: monitoring_enabled (dynamic, boolean)
    Methods:
        1: reset_counters
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SAG_SWELL_MONITOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    sag_threshold_percent: int = 90
    swell_threshold_percent: int = 110
    sag_count: int = 0
    swell_count: int = 0
    sag_duration_ms: int = 0
    swell_duration_ms: int = 0
    last_sag_depth_percent: int = 100
    last_swell_magnitude_percent: int = 100
    monitoring_enabled: bool = True

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="sag_threshold_percent"),
        3: AttributeDescription(attribute_id=3, attribute_name="swell_threshold_percent"),
        4: AttributeDescription(attribute_id=4, attribute_name="sag_count"),
        5: AttributeDescription(attribute_id=5, attribute_name="swell_count"),
        6: AttributeDescription(attribute_id=6, attribute_name="sag_duration_ms"),
        7: AttributeDescription(attribute_id=7, attribute_name="swell_duration_ms"),
        8: AttributeDescription(attribute_id=8, attribute_name="last_sag_depth_percent"),
        9: AttributeDescription(attribute_id=9, attribute_name="last_swell_magnitude_percent"),
        10: AttributeDescription(attribute_id=10, attribute_name="monitoring_enabled"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset_counters"}

    def set_sag_threshold_percent(self, threshold: int) -> None:
        """Set sag threshold as percentage of nominal voltage."""
        self.sag_threshold_percent = max(0, min(100, threshold))

    def set_swell_threshold_percent(self, threshold: int) -> None:
        """Set swell threshold as percentage of nominal voltage."""
        self.swell_threshold_percent = max(100, min(200, threshold))

    def get_sag_count(self) -> int:
        """Get total sag count."""
        return self.sag_count

    def get_swell_count(self) -> int:
        """Get total swell count."""
        return self.swell_count

    def record_sag(self, depth_percent: int, duration_ms: int) -> None:
        """Record a voltage sag event."""
        self.sag_count += 1
        self.last_sag_depth_percent = max(0, min(100, depth_percent))
        self.sag_duration_ms = duration_ms

    def record_swell(self, magnitude_percent: int, duration_ms: int) -> None:
        """Record a voltage swell event."""
        self.swell_count += 1
        self.last_swell_magnitude_percent = max(100, min(200, magnitude_percent))
        self.swell_duration_ms = duration_ms

    def get_last_sag_depth_percent(self) -> int:
        """Get last sag depth as percentage."""
        return self.last_sag_depth_percent

    def get_last_swell_magnitude_percent(self) -> int:
        """Get last swell magnitude as percentage."""
        return self.last_swell_magnitude_percent

    def get_sag_duration_ms(self) -> int:
        """Get last sag duration in milliseconds."""
        return self.sag_duration_ms

    def get_swell_duration_ms(self) -> int:
        """Get last swell duration in milliseconds."""
        return self.swell_duration_ms

    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.monitoring_enabled

    def set_monitoring_enabled(self, enabled: bool) -> None:
        """Enable or disable monitoring."""
        self.monitoring_enabled = enabled

    def check_voltage(self, voltage_percent: int) -> str:
        """Check voltage level and return status.

        Returns:
            'normal', 'sag', or 'swell'
        """
        if not self.monitoring_enabled:
            return 'normal'

        if voltage_percent < self.sag_threshold_percent:
            return 'sag'
        elif voltage_percent > self.swell_threshold_percent:
            return 'swell'
        return 'normal'

    def get_total_events(self) -> int:
        """Get total number of events."""
        return self.sag_count + self.swell_count

    def reset_counters(self) -> None:
        """Method 1: Reset all event counters."""
        self.sag_count = 0
        self.swell_count = 0
        self.sag_duration_ms = 0
        self.swell_duration_ms = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
