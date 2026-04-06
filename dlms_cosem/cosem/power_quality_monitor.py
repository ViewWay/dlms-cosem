"""IC class 200 - Power Quality Monitor.

Monitors power quality parameters including voltage, current,
and frequency deviations.

Custom IC class for advanced power quality monitoring.
"""
from typing import ClassVar, Dict

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class PowerQualityMonitor:
    """COSEM IC Power Quality Monitor (class_id=200).

    Attributes:
        1: logical_name (static)
        2: voltage_sag_count (dynamic, double-long-unsigned)
        3: voltage_swell_count (dynamic, double-long-unsigned)
        4: interruption_count (dynamic, double-long-unsigned)
        5: voltage_unbalance (dynamic, unsigned)
        6: frequency_deviation (dynamic, integer)
        7: thd_voltage (dynamic, unsigned)
        8: thd_current (dynamic, unsigned)
        9: power_factor_avg (dynamic, unsigned)
    Methods:
        1: reset_counters
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.POWER_QUALITY_MONITOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    voltage_sag_count: int = 0
    voltage_swell_count: int = 0
    interruption_count: int = 0
    voltage_unbalance: int = 0
    frequency_deviation: int = 0
    thd_voltage: int = 0
    thd_current: int = 0
    power_factor_avg: int = 100

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="voltage_sag_count"),
        3: AttributeDescription(attribute_id=3, attribute_name="voltage_swell_count"),
        4: AttributeDescription(attribute_id=4, attribute_name="interruption_count"),
        5: AttributeDescription(attribute_id=5, attribute_name="voltage_unbalance"),
        6: AttributeDescription(attribute_id=6, attribute_name="frequency_deviation"),
        7: AttributeDescription(attribute_id=7, attribute_name="thd_voltage"),
        8: AttributeDescription(attribute_id=8, attribute_name="thd_current"),
        9: AttributeDescription(attribute_id=9, attribute_name="power_factor_avg"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset_counters"}

    def increment_sag(self) -> None:
        """Increment voltage sag counter."""
        self.voltage_sag_count += 1

    def increment_swell(self) -> None:
        """Increment voltage swell counter."""
        self.voltage_swell_count += 1

    def increment_interruption(self) -> None:
        """Increment interruption counter."""
        self.interruption_count += 1

    def set_voltage_unbalance(self, unbalance: int) -> None:
        """Set voltage unbalance as percentage."""
        self.voltage_unbalance = max(0, min(100, unbalance))

    def set_frequency_deviation(self, deviation: int) -> None:
        """Set frequency deviation in centi-Hz."""
        self.frequency_deviation = deviation

    def set_thd_voltage(self, thd: int) -> None:
        """Set Total Harmonic Distortion for voltage as percentage."""
        self.thd_voltage = max(0, min(100, thd))

    def set_thd_current(self, thd: int) -> None:
        """Set Total Harmonic Distortion for current as percentage."""
        self.thd_current = max(0, min(100, thd))

    def set_power_factor_avg(self, pf: int) -> None:
        """Set average power factor as percentage (0-100)."""
        self.power_factor_avg = max(0, min(100, pf))

    def get_power_factor_decimal(self) -> float:
        """Get power factor as decimal (0.0-1.0)."""
        return self.power_factor_avg / 100.0

    def get_total_events(self) -> int:
        """Get total number of power quality events."""
        return self.voltage_sag_count + self.voltage_swell_count + self.interruption_count

    def reset_counters(self) -> None:
        """Method 1: Reset all event counters."""
        self.voltage_sag_count = 0
        self.voltage_swell_count = 0
        self.interruption_count = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
