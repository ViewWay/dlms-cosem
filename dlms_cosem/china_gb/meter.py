"""China GB standard smart meter model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from dlms_cosem.china_gb.frame import GBRS485Config, GBCp28Frame
from dlms_cosem.china_gb.tariff import GBTariffProfile
from dlms_cosem.china_gb.types import GBCp28Command, GBTimeSeason, GBTariffType


@dataclass
class GBMeter:
    """China GB standard smart meter model."""

    def __init__(self, address: str = "000000000000"):
        self.address = address
        self.tariff_profile = GBTariffProfile()
        self.rs485_config = GBRS485Config()
        self.registers: Dict[str, float] = {}

    def set_tariff_profile(self, profile: GBTariffProfile) -> None:
        self.tariff_profile = profile

    def read_register(self, obis: str) -> Optional[float]:
        return self.registers.get(obis)

    def write_register(self, obis: str, value: float) -> None:
        self.registers[obis] = value

    def create_cp28_frame(self, command: GBCp28Command, data: bytes = b"") -> GBCp28Frame:
        """Create a CP 28 frame for this meter."""
        return GBCp28Frame(
            address=self.address.encode("ascii")[:6].ljust(6, b"\x00"),
            command=command,
            data=data,
        )

    def setup_china_standard_tariff(self) -> None:
        """Setup standard China time-of-use tariff.

        Typical 4-rate tariff:
        - Peak: 08:00-11:00, 18:00-21:00
        - Shoulder: 07:00-08:00, 11:00-18:00
        - Flat: 21:00-23:00
        - Valley: 23:00-07:00
        """
        from dlms_cosem.china_gb.tariff import GBTariffSchedule

        profile = GBTariffProfile(name="China Standard 4-Rate")

        # Summer (and default)
        for season in [GBTimeSeason.SPRING, GBTimeSeason.SUMMER,
                       GBTimeSeason.AUTUMN, GBTimeSeason.WINTER]:
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.PEAK,
                hour_start=8, minute_start=0,
                hour_end=11, minute_end=0,
                season=season,
            ))
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.PEAK,
                hour_start=18, minute_start=0,
                hour_end=21, minute_end=0,
                season=season,
            ))
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.SHOULDER,
                hour_start=7, minute_start=0,
                hour_end=8, minute_end=0,
                season=season,
            ))
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.SHOULDER,
                hour_start=11, minute_start=0,
                hour_end=18, minute_end=0,
                season=season,
            ))
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.FLAT,
                hour_start=21, minute_start=0,
                hour_end=23, minute_end=0,
                season=season,
            ))
            profile.add_schedule(GBTariffSchedule(
                tariff_type=GBTariffType.VALLEY,
                hour_start=23, minute_start=0,
                hour_end=7, minute_end=0,
                season=season,
            ))

        self.tariff_profile = profile
