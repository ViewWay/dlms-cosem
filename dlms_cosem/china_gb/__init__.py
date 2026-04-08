"""China GB/T 17215.301 extensions for DLMS/COSEM.

This module provides lazy-loaded imports to reduce memory footprint.
"""
from __future__ import annotations

__all__ = [
    # Enums
    "GBTariffType",
    "GBTimeSeason",
    "GBCp28Command",
    "GBPhase",
    # Classes
    "GBTariffSchedule",
    "GBTariffProfile",
    "GBRS485Config",
    "GBCp28Frame",
    "GBMeter",
    "GBTariffMapper",
]


def __getattr__(name: str):
    """Lazy import China GB classes on first access."""
    # Enums
    if name == "GBTariffType":
        from dlms_cosem.china_gb.types import GBTariffType
        return GBTariffType
    if name == "GBTimeSeason":
        from dlms_cosem.china_gb.types import GBTimeSeason
        return GBTimeSeason
    if name == "GBCp28Command":
        from dlms_cosem.china_gb.types import GBCp28Command
        return GBCp28Command
    if name == "GBPhase":
        from dlms_cosem.china_gb.types import GBPhase
        return GBPhase

    # Classes
    if name == "GBTariffSchedule":
        from dlms_cosem.china_gb.tariff import GBTariffSchedule
        return GBTariffSchedule
    if name == "GBTariffProfile":
        from dlms_cosem.china_gb.tariff import GBTariffProfile
        return GBTariffProfile
    if name == "GBRS485Config":
        from dlms_cosem.china_gb.frame import GBRS485Config
        return GBRS485Config
    if name == "GBCp28Frame":
        from dlms_cosem.china_gb.frame import GBCp28Frame
        return GBCp28Frame
    if name == "GBMeter":
        from dlms_cosem.china_gb.meter import GBMeter
        return GBMeter
    if name == "GBTariffMapper":
        from dlms_cosem.china_gb.obis import GBTariffMapper
        return GBTariffMapper

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
