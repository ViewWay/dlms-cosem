"""China GB OBIS extensions and mappings."""
from __future__ import annotations

from typing import Dict

from dlms_cosem.china_gb.types import GBTariffType, GBPhase


class GBTariffMapper:
    """Map between China GB tariff types and COSEM register attributes."""

    # China GB OBIS extensions for energy metering
    GB_OBIS_EXTENSIONS = {
        # Active energy by tariff (import)
        "1.0.0.8.0.0": "Total Active Energy Import",
        "1.0.1.8.0.0": "Peak Active Energy Import",
        "1.0.2.8.0.0": "Shoulder Active Energy Import",
        "1.0.3.8.0.0": "Flat Active Energy Import",
        "1.0.4.8.0.0": "Valley Active Energy Import",
        # Reactive energy by tariff
        "2.0.0.8.0.0": "Total Reactive Energy Import",
        "2.0.1.8.0.0": "Peak Reactive Energy Import",
        # Demand by tariff
        "1.0.0.1.0.0": "Total Maximum Demand",
        "1.0.1.1.0.0": "Peak Maximum Demand",
        # Voltage and current per phase
        "1.0.31.7.0.0": "Voltage Phase A",
        "1.0.52.7.0.0": "Voltage Phase B",
        "1.0.73.7.0.0": "Voltage Phase C",
        "1.0.51.5.0.0": "Current Phase A",
        "1.0.71.5.0.0": "Current Phase B",
        "1.0.91.5.0.0": "Current Phase C",
        # Power factor per phase
        "1.0.80.82.0.0": "Power Factor Phase A",
        "1.0.81.82.0.0": "Power Factor Phase B",
        "1.0.82.82.0.0": "Power Factor Phase C",
        # Frequency
        "1.0.14.7.0.0": "Frequency",
        # Clock
        "0.0.1.0.0.0": "Meter Date/Time",
        # Meter info
        "0.0.96.1.0.0": "Server ID",
        "0.0.96.1.1.0": "Meter Model",
        "0.0.96.1.2.0": "Firmware Version",
        "0.0.96.1.3.0": "Manufacturer",
        # Billing date
        "0.0.96.10.1.0": "Billing Date 1",
        "0.0.96.10.2.0": "Billing Date 2",
        # Load profile
        "1.0.99.1.0.0": "Load Profile",
    }

    @classmethod
    def get_obis_name(cls, obis: str) -> str:
        """Get descriptive name for GB OBIS code."""
        return cls.GB_OBIS_EXTENSIONS.get(obis, "Unknown")

    @classmethod
    def get_energy_obis(cls, direction: int = 1, tariff: GBTariffType = GBTariffType.TOTAL) -> str:
        """Get OBIS for energy register.

        Args:
            direction: 1=import, 2=export
            tariff: Tariff type
        """
        return f"{direction}.0.{tariff.value}.8.0.0"

    @classmethod
    def get_demand_obis(cls, tariff: GBTariffType = GBTariffType.TOTAL) -> str:
        """Get OBIS for demand register."""
        return f"1.0.{tariff.value}.1.0.0"

    @classmethod
    def get_voltage_obis(cls, phase: GBPhase = GBPhase.COMBINED) -> str:
        """Get OBIS for voltage register."""
        phase_map = {0: 31, 1: 52, 2: 73}
        code = phase_map.get(phase.value, 31)
        return f"1.0.{code}.7.0.0"

    @classmethod
    def get_current_obis(cls, phase: GBPhase = GBPhase.COMBINED) -> str:
        """Get OBIS for current register."""
        phase_map = {0: 51, 1: 71, 2: 91}
        code = phase_map.get(phase.value, 51)
        return f"1.0.{code}.5.0.0"

    @classmethod
    def parse_obis_code(cls, obis: str) -> dict:
        """Parse OBIS code into components."""
        parts = obis.split(".")
        if len(parts) != 6:
            return {"error": "Invalid OBIS code", "raw": obis}

        return {
            "group_a": int(parts[0]),
            "group_b": int(parts[1]),
            "group_c": int(parts[2]),
            "group_d": int(parts[3]),
            "group_e": int(parts[4]),
            "group_f": int(parts[5]),
            "name": cls.get_obis_name(obis),
        }
