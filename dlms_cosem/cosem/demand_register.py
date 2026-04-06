"""IC class 5 - Demand Register.

Records the maximum (demand) value over a sliding or fixed window period.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.5
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class DemandRegister:
    """COSEM IC Demand Register (class_id=5).

    Attributes:
        1: logical_name (static)
        2: current_value (dynamic)
        3: last_average_value (dynamic)
        4: status (dynamic, bitstring)
        5: capture_time (dynamic, octet-string datetime)
        6: period (static)
        7: number_of_periods (static)
    Methods:
        1: reset
        2: next_period
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.DEMAND_REGISTER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    current_value: Optional[Any] = None
    last_average_value: Optional[Any] = None
    status: int = 0
    capture_time: Optional[datetime] = None
    period: int = 0
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
        3: AttributeDescription(attribute_id=3, attribute_name="last_average_value"),
        4: AttributeDescription(attribute_id=4, attribute_name="status"),
        5: AttributeDescription(attribute_id=5, attribute_name="capture_time"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "next_period"}

    def reset(self) -> None:
        self.current_value = 0
        self.last_average_value = 0

    def next_period(self) -> None:
        """Method 2: Advance to next demand period."""
        self.last_average_value = self.current_value
        self.current_value = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
