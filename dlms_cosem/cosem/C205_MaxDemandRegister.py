"""IC004 - Maximum Demand Register.

Records maximum demand (peak power) with associated timestamps
and period configuration. Extends the demand register concept
for maximum value tracking.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.5
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class MaxDemandRegister:
    """COSEM IC Maximum Demand Register (class_id=5, variant).

    Tracks the maximum demand value recorded over sliding/fixed windows.

    Attributes:
        1: logical_name (static)
        2: current_value (dynamic)
        3: last_max_value (dynamic)
        4: last_max_time (dynamic, datetime)
        5: status (dynamic, bitstring)
        6: period (static, seconds)
        7: number_of_periods (static)
    Methods:
        1: reset
        2: next_period
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.DEMAND_REGISTER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    current_value: Optional[Any] = None
    last_max_value: Optional[Any] = None
    last_max_time: Optional[datetime] = None
    status: int = 0
    period: int = 900  # default 15 min
    number_of_periods: int = 1
    scaler: int = 0
    unit: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        6: AttributeDescription(attribute_id=6, attribute_name="period"),
        7: AttributeDescription(attribute_id=7, attribute_name="number_of_periods"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="current_value"),
        3: AttributeDescription(attribute_id=3, attribute_name="last_max_value"),
        4: AttributeDescription(attribute_id=4, attribute_name="last_max_time"),
        5: AttributeDescription(attribute_id=5, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "next_period"}

    def update_demand(self, value: Any, timestamp: Optional[datetime] = None) -> None:
        """Update demand tracking. Records new max if exceeded."""
        if self.last_max_value is None or value > self.last_max_value:
            self.last_max_value = value
            self.last_max_time = timestamp or datetime.now()

    def reset(self) -> None:
        self.current_value = 0
        self.last_max_value = 0
        self.last_max_time = None

    def next_period(self) -> None:
        self.last_max_value = self.current_value
        self.current_value = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
