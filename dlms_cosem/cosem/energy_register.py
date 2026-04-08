"""Energy Register - Cumulative energy measurement.

Provides registers for active, reactive, and apparent energy in all quadrants.
OBIS codes follow GB/T 17215 Chinese standard.

Common OBIS codes:
  Active+   : 1.0.1.8.0.255 (total), 1.0.1.8.1.255 (T1), ...
  Active-   : 1.0.2.8.0.255
  Reactive+ : 1.0.3.8.0.255
  Reactive- : 1.0.4.8.0.255
  Q1        : 1.0.5.8.0.255
  Q2        : 1.0.6.8.0.255
  Q3        : 1.0.7.8.0.255
  Q4        : 1.0.8.8.0.255
  Apparent+ : 1.0.9.8.0.255
  Apparent- : 1.0.10.8.0.255
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C3_Register import Register


# GB/T 17215 standard OBIS codes for energy registers
OBIS_ACTIVE_IMPORT = "1.0.1.8.0.255"
OBIS_ACTIVE_EXPORT = "1.0.2.8.0.255"
OBIS_REACTIVE_IMPORT = "1.0.3.8.0.255"
OBIS_REACTIVE_EXPORT = "1.0.4.8.0.255"
OBIS_Q1 = "1.0.5.8.0.255"
OBIS_Q2 = "1.0.6.8.0.255"
OBIS_Q3 = "1.0.7.8.0.255"
OBIS_Q4 = "1.0.8.8.0.255"
OBIS_APPARENT_IMPORT = "1.0.9.8.0.255"
OBIS_APPARENT_EXPORT = "1.0.10.8.0.255"

# Tariff-specific: e.g., 1.0.1.8.1.255 = T1, 1.0.1.8.2.255 = T2, etc.


def create_energy_register(obis_str: str, value: Any = 0, scaler: int = -3,
                           unit: int = 1) -> Register:
    """Factory to create an energy Register with standard OBIS.

    Args:
        obis_str: OBIS code string (e.g., "1.0.1.8.0.255")
        value: Initial energy value
        scaler: Scaler (typically -3 for Wh → kWh)
        unit: Unit code (1 = Wh)
    """
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
