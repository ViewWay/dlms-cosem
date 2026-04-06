"""Power Register - Instantaneous power measurement.

Provides registers for instantaneous active, reactive, and apparent power.

Common OBIS codes:
  Active Power   : 1.0.11.7.0.255
  Reactive Power : 1.0.13.7.0.255
  Apparent Power : 1.0.15.7.0.255
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C3_Register import Register

OBIS_ACTIVE_POWER = "1.0.11.7.0.255"
OBIS_REACTIVE_POWER = "1.0.13.7.0.255"
OBIS_APPARENT_POWER = "1.0.15.7.0.255"


def create_power_register(obis_str: str, value: Any = 0, scaler: int = -1,
                          unit: int = 27) -> Register:
    """Factory to create a power Register with standard OBIS.

    Args:
        obis_str: OBIS code string
        value: Initial power value
        scaler: Scaler (typically -1 for W → kW)
        unit: Unit code (27 = W)
    """
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
