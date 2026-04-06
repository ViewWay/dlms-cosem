"""IC class 201 - Harmonic Monitor.

Monitors harmonic distortion in voltage and current waveforms.
Used in power quality analysis and compliance monitoring.

Custom IC class for advanced harmonic analysis.
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


class MonitoringMode:
    """Harmonic monitoring modes."""
    VOLTAGE_ONLY = 0
    CURRENT_ONLY = 1
    BOTH = 2


@attr.s(auto_attribs=True)
class HarmonicMonitor:
    """COSEM IC Harmonic Monitor (class_id=201).

    Attributes:
        1: logical_name (static)
        2: voltage_harmonics (dynamic, array of unsigned, up to 63)
        3: current_harmonics (dynamic, array of unsigned, up to 63)
        4: thd_voltage (dynamic, unsigned)
        5: thd_current (dynamic, unsigned)
        6: monitoring_mode (dynamic, enum)
        7: sample_rate (dynamic, unsigned)
    Methods:
        1: calculate_thd
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.HARMONIC_MONITOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    voltage_harmonics: List[int] = attr.ib(factory=lambda: [0] * 63)
    current_harmonics: List[int] = attr.ib(factory=lambda: [0] * 63)
    thd_voltage: int = 0
    thd_current: int = 0
    monitoring_mode: int = MonitoringMode.BOTH
    sample_rate: int = 256

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="voltage_harmonics"),
        3: AttributeDescription(attribute_id=3, attribute_name="current_harmonics"),
        4: AttributeDescription(attribute_id=4, attribute_name="thd_voltage"),
        5: AttributeDescription(attribute_id=5, attribute_name="thd_current"),
        6: AttributeDescription(attribute_id=6, attribute_name="monitoring_mode"),
        7: AttributeDescription(attribute_id=7, attribute_name="sample_rate"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "calculate_thd"}

    def get_voltage_harmonic(self, order: int) -> int:
        """Get voltage harmonic by order (1-63)."""
        if 1 <= order <= 63:
            return self.voltage_harmonics[order - 1]
        return 0

    def set_voltage_harmonic(self, order: int, value: int) -> bool:
        """Set voltage harmonic by order (1-63)."""
        if 1 <= order <= 63:
            self.voltage_harmonics[order - 1] = max(0, min(255, value))
            return True
        return False

    def get_current_harmonic(self, order: int) -> int:
        """Get current harmonic by order (1-63)."""
        if 1 <= order <= 63:
            return self.current_harmonics[order - 1]
        return 0

    def set_current_harmonic(self, order: int, value: int) -> bool:
        """Set current harmonic by order (1-63)."""
        if 1 <= order <= 63:
            self.current_harmonics[order - 1] = max(0, min(255, value))
            return True
        return False

    def set_thd_voltage(self, thd: int) -> None:
        """Set THD for voltage as percentage."""
        self.thd_voltage = max(0, min(100, thd))

    def set_thd_current(self, thd: int) -> None:
        """Set THD for current as percentage."""
        self.thd_current = max(0, min(100, thd))

    def set_monitoring_mode(self, mode: int) -> None:
        """Set monitoring mode."""
        self.monitoring_mode = mode

    def get_monitoring_mode_name(self) -> str:
        """Get monitoring mode name as string."""
        names = {
            MonitoringMode.VOLTAGE_ONLY: "Voltage Only",
            MonitoringMode.CURRENT_ONLY: "Current Only",
            MonitoringMode.BOTH: "Both",
        }
        return names.get(self.monitoring_mode, "Unknown")

    def set_sample_rate(self, rate: int) -> None:
        """Set sample rate in samples per second."""
        self.sample_rate = max(1, rate)

    def calculate_thd_voltage(self) -> int:
        """Calculate THD for voltage based on harmonics."""
        if len(self.voltage_harmonics) < 2:
            return 0
        fundamental = self.voltage_harmonics[0]
        if fundamental == 0:
            return 0
        sum_squares = sum(h ** 2 for h in self.voltage_harmonics[1:])
        thd = (sum_squares ** 0.5 / fundamental) * 100
        self.thd_voltage = int(min(100, thd))
        return self.thd_voltage

    def calculate_thd_current(self) -> int:
        """Calculate THD for current based on harmonics."""
        if len(self.current_harmonics) < 2:
            return 0
        fundamental = self.current_harmonics[0]
        if fundamental == 0:
            return 0
        sum_squares = sum(h ** 2 for h in self.current_harmonics[1:])
        thd = (sum_squares ** 0.5 / fundamental) * 100
        self.thd_current = int(min(100, thd))
        return self.thd_current

    def calculate_thd(self) -> None:
        """Method 1: Calculate THD for both voltage and current."""
        self.calculate_thd_voltage()
        self.calculate_thd_current()

    def reset_harmonics(self) -> None:
        """Reset all harmonic values to zero."""
        self.voltage_harmonics = [0] * 63
        self.current_harmonics = [0] * 63

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
