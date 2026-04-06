"""Voltage measurement registers.

OBIS codes (GB/T 17215):
  Phase A: 1.0.32.7.0.255
  Phase B: 1.0.52.7.0.255
  Phase C: 1.0.72.7.0.255
  Average: 1.0.92.7.0.255
"""
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C3_Register import Register

OBIS_VOLTAGE_A = "1.0.32.7.0.255"
OBIS_VOLTAGE_B = "1.0.52.7.0.255"
OBIS_VOLTAGE_C = "1.0.72.7.0.255"
OBIS_VOLTAGE_AVG = "1.0.92.7.0.255"


def create_voltage_register(obis_str: str = OBIS_VOLTAGE_A, value: float = 220.0,
                            scaler: int = -1, unit: int = 7) -> Register:
    """Factory to create a voltage Register. Unit 7 = V."""
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
