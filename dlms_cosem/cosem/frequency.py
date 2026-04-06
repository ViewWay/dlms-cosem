"""Frequency measurement register.

OBIS code: 1.0.14.7.0.255
"""
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C3_Register import Register

OBIS_FREQUENCY = "1.0.14.7.0.255"


def create_frequency_register(obis_str: str = OBIS_FREQUENCY, value: float = 50.0,
                              scaler: int = -2, unit: int = 10) -> Register:
    """Factory to create a frequency Register. Unit 10 = Hz."""
    return Register(
        logical_name=Obis.from_string(obis_str),
        value=value,
        scaler=scaler,
        unit=unit,
    )
