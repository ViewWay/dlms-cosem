"""China GB/T 17215.301 extensions for DLMS/COSEM."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Tuple, Dict

import structlog

from dlms_cosem.cosem.obis import Obis

LOG = structlog.get_logger()


class GBTariffType(IntEnum):
    """China GB tariff/rate types."""
    TOTAL = 0
    PEAK = 1
    SHOULDER = 2
    FLAT = 3
    VALLEY = 4
    SPIKE = 5  # 特殊尖峰


class GBTimeSeason(IntEnum):
    """China time-of-use seasons."""
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


class GBCp28Command(IntEnum):
    """DLMS/T CP 28 command codes (China local protocol)."""
    READ_DATA = 0x01
    WRITE_DATA = 0x02
    BROADCAST_TIME = 0x03
    SET_ADDRESS = 0x04
    CHANGE_BAUD = 0x05
    CLEAR_METER = 0x06
    FROZEN_COMMAND = 0x08
    CHANGE_PASSWORD = 0x0A
    MAX_DEMAND_CLEAR = 0x0C
    RELAY_CONTROL = 0x10


class GBPhase(IntEnum):
    """Phase designations."""
    PHASE_A = 0
    PHASE_B = 1
    PHASE_C = 2
    COMBINED = 3


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
                    # Cross-midnight schedule
                    if current_minutes >= start or current_minutes < end:
                        return sched.tariff_type
                else:
                    if start <= current_minutes < end:
                        return sched.tariff_type
        return GBTariffType.FLAT

    def get_all_seasons(self) -> List[GBTimeSeason]:
        return list(set(s.season for s in self.schedules))


@dataclass
class GBRS485Config:
    """China standard RS485 communication parameters."""
    baud_rate: int = 2400
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "even"  # even, odd, none
    address_length: int = 12  # meter address length (bytes)
    password: Optional[bytes] = None
    timeout_ms: int = 5000

    @property
    def parity_char(self) -> str:
        return {"even": "E", "odd": "O", "none": "N"}[self.parity]

    @property
    def serial_config(self) -> str:
        return f"{self.baud_rate},{self.data_bits},{self.parity_char},{self.stop_bits}"

    @classmethod
    def from_string(cls, config: str) -> "GBRS485Config":
        """Parse serial config string like '2400,8,E,1'."""
        parts = config.split(",")
        return cls(
            baud_rate=int(parts[0]),
            data_bits=int(parts[1]),
            parity={"E": "even", "O": "odd", "N": "none"}[parts[2]],
            stop_bits=int(parts[3]),
        )


@dataclass
class GBCp28Frame:
    """DLMS/T CP 28 frame (China local protocol frame)."""
    address: bytes
    control: int = 0x13
    command: GBCp28Command = GBCp28Command.READ_DATA
    data_length: int = 0
    data: bytes = b""
    checksum: int = 0

    def to_bytes(self) -> bytes:
        """Encode CP 28 frame."""
        frame = bytearray()
        frame.append(0x68)  # Start
        frame.extend(self.address)
        frame.append(self.control)
        frame.append(self.command)
        frame.append(len(self.data))
        frame.extend(self.data)
        # Checksum: XOR of all bytes after start marker
        checksum = 0
        for b in frame[1:]:
            checksum ^= b
        frame.append(checksum)
        frame.append(0x16)  # End
        return bytes(frame)

    @classmethod
    def from_bytes(cls, data: bytes) -> "GBCp28Frame":
        """Decode CP 28 frame."""
        if len(data) < 10 or data[0] != 0x68:
            raise ValueError("Invalid CP 28 frame")

        addr_len = 6  # Standard address length
        address = data[1:1 + addr_len]
        control = data[1 + addr_len]
        command = GBCp28Command(data[2 + addr_len])
        data_len = data[3 + addr_len]
        payload = data[4 + addr_len:4 + addr_len + data_len]
        checksum = data[4 + addr_len + data_len]

        return cls(
            address=address,
            control=control,
            command=command,
            data_length=data_len,
            data=payload,
            checksum=checksum,
        )


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
