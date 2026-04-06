"""IC class 112 - Credit.

Credit management for prepaid metering.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.6.2
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Credit:
    """COSEM IC Credit (class_id=112).

    Attributes:
        1: logical_name (static)
        2: current_credit_amount (dynamic) - Current credit balance
        3: type (dynamic) - Type of credit
        4: priority (dynamic) - Priority level
        5: warning_threshold (dynamic) - Low credit warning threshold
        6: limit (dynamic) - Credit limit
        7: credit_configuration (dynamic) - Credit configuration
        8: status (dynamic) - Credit status
    Methods:
        1: reset
        2: update_credit_amount
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CREDIT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    current_credit_amount: float = 0.0
    type: int = 0
    priority: int = 0
    warning_threshold: float = 0.0
    limit: float = 0.0
    credit_configuration: int = 0
    status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="current_credit_amount"),
        3: AttributeDescription(attribute_id=3, attribute_name="type"),
        4: AttributeDescription(attribute_id=4, attribute_name="priority"),
        5: AttributeDescription(attribute_id=5, attribute_name="warning_threshold"),
        6: AttributeDescription(attribute_id=6, attribute_name="limit"),
        7: AttributeDescription(attribute_id=7, attribute_name="credit_configuration"),
        8: AttributeDescription(attribute_id=8, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "update_credit_amount",
    }

    def reset(self) -> None:
        """Method 1: Reset credit to defaults."""
        self.current_credit_amount = 0.0
        self.status = 0

    def update_credit_amount(self, amount: float) -> None:
        """Method 2: Update credit amount."""
        self.current_credit_amount += amount
        if self.current_credit_amount < 0:
            self.current_credit_amount = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def is_low_credit(self) -> bool:
        """Check if credit is below warning threshold."""
        return self.current_credit_amount <= self.warning_threshold

    def is_credit_available(self) -> bool:
        """Check if credit is available."""
        return self.current_credit_amount > 0
