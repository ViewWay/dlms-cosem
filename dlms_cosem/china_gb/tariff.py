"""China GB tariff schedule and profile management."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from dlms_cosem.china_gb.types import GBTariffType, GBTimeSeason


@dataclass
class GBTariffSchedule:
    """China tariff schedule entry."""
    tariff_type: GBTariffType
    hour_start: int
    minute_start: int
    hour_end: int
    minute_end: int
    season: GBTimeSeason = GBTimeSeason.SPRING
    price: Optional[float] = None

    @property
    def duration_minutes(self) -> int:
        end = self.hour_end * 60 + self.minute_end
        start = self.hour_start * 60 + self.minute_start
        if end <= start:
            end += 24 * 60
        return end - start


@dataclass
class GBTariffProfile:
    """Complete China tariff profile with all seasons."""
    name: str = "Default"
    schedules: List[GBTariffSchedule] = field(default_factory=list)

    def add_schedule(self, schedule: GBTariffSchedule) -> None:
        self.schedules.append(schedule)

    def get_current_tariff(self, hour: int, minute: int, season: GBTimeSeason) -> GBTariffType:
        """Get active tariff type for given time."""
        current_minutes = hour * 60 + minute
        for sched in self.schedules:
            if sched.season == season:
                start = sched.hour_start * 60 + sched.minute_start
                end = sched.hour_end * 60 + sched.minute_end
                if end <= start:
                    if current_minutes >= start or current_minutes < end:
                        return sched.tariff_type
                else:
                    if start <= current_minutes < end:
                        return sched.tariff_type
        return GBTariffType.FLAT

    def get_all_seasons(self) -> List[GBTimeSeason]:
        return list(set(s.season for s in self.schedules))
