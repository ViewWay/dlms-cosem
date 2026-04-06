"""Current measurement registers.

OBIS codes (GB/T 17215):
  Phase A: 1.0.31.7.0.255
  Phase B: 1.0.51.7.0.255
  Phase C: 1.0.71.7.0.255
  Average: 1.0.91.7.0.255
"""
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.register import Register

OBIS_CURRENT_A = "1.0.31.7.0.255"
OBIS_CURRENT_B = "1.0.51.7.0.255"
OBIS_CURRENT_C = "1.0.71.7.0.255"
OBIS_CURRENT_AVG = "1.0.91.7.0.255"


def create_current_register(obis_str: str = OBIS_CURRENT_A, value: float = 5.0,
                            scaler: int = -1, unit: int = 5) -> Register:
    """Factory to create a current Register. Unit 5 = A."""
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
