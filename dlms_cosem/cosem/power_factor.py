"""Power Factor measurement registers.

OBIS codes:
  Total: 1.0.13.7.0.255 (pf)
  Phase A: 1.0.33.7.0.255
  Phase B: 1.0.53.7.0.255
  Phase C: 1.0.73.7.0.255
"""
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.register import Register

OBIS_PF_TOTAL = "1.0.13.7.0.255"
OBIS_PF_A = "1.0.33.7.0.255"
OBIS_PF_B = "1.0.53.7.0.255"
OBIS_PF_C = "1.0.73.7.0.255"


def create_pf_register(obis_str: str = OBIS_PF_TOTAL, value: float = 1.0,
                       scaler: int = -2, unit: int = 106) -> Register:
    """Factory to create a power factor Register. Unit 106 = dimensionless."""
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
