"""IC class 113 - Charge.

Charge management for billing and tariffication.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.6.3
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Charge:
    """COSEM IC Charge (class_id=113).

    Attributes:
        1: logical_name (static)
        2: total_amount (dynamic) - Total charge amount
        3: charge_type (dynamic) - Type of charge
        4: priority (dynamic) - Priority level
        5: unit_charge (dynamic) - Unit charge rate
        6: unit_charge_active (dynamic) - Active unit charge rate
        7: last_execution_time (dynamic) - Time of last execution
        8: execution_period (dynamic) - Period between executions
        9: total_amount_published (dynamic) - Published total amount
    Methods:
        1: reset
        2: update_total_amount
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CHARGE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    total_amount: float = 0.0
    charge_type: int = 0
    priority: int = 0
    unit_charge: float = 0.0
    unit_charge_active: float = 0.0
    last_execution_time: Optional[bytes] = None
    execution_period: int = 0
    total_amount_published: float = 0.0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="total_amount"),
        3: AttributeDescription(attribute_id=3, attribute_name="charge_type"),
        4: AttributeDescription(attribute_id=4, attribute_name="priority"),
        5: AttributeDescription(attribute_id=5, attribute_name="unit_charge"),
        6: AttributeDescription(attribute_id=6, attribute_name="unit_charge_active"),
        7: AttributeDescription(attribute_id=7, attribute_name="last_execution_time"),
        8: AttributeDescription(attribute_id=8, attribute_name="execution_period"),
        9: AttributeDescription(attribute_id=9, attribute_name="total_amount_published"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "update_total_amount",
    }

    def reset(self) -> None:
        """Method 1: Reset charge to defaults."""
        self.total_amount = 0.0
        self.unit_charge_active = 0.0
        self.last_execution_time = None
        self.total_amount_published = 0.0

    def update_total_amount(self, amount: float) -> None:
        """Method 2: Update total charge amount."""
        self.total_amount += amount

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def calculate_charge(self, units: float) -> float:
        """Calculate charge for given units."""
        return units * self.unit_charge_active
