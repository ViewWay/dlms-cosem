"""China GB/T 17215.301 type definitions."""
from __future__ import annotations

from enum import IntEnum


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
