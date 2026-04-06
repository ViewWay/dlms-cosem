"""IC class 111 - Account.

Account management for prepaid metering.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.6.1
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class Account:
    """COSEM IC Account (class_id=111).

    Attributes:
        1: logical_name (static)
        2: account_status (dynamic) - Status of the account
        3: current_credit_amount (dynamic) - Current credit balance
        4: current_debit_amount (dynamic) - Current debit amount
        5: credit_in_use (dynamic) - Credit currently being used
        6: available_credit (dynamic) - Available credit
        7: emergency_credit_limit (dynamic) - Emergency credit limit
        8: emergency_credit_threshold (dynamic) - Threshold for emergency credit
        9: emergency_credit_status (dynamic) - Status of emergency credit
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ACCOUNT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    account_status: int = 0
    current_credit_amount: float = 0.0
    current_debit_amount: float = 0.0
    credit_in_use: float = 0.0
    available_credit: float = 0.0
    emergency_credit_limit: float = 0.0
    emergency_credit_threshold: float = 0.0
    emergency_credit_status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="account_status"),
        3: AttributeDescription(attribute_id=3, attribute_name="current_credit_amount"),
        4: AttributeDescription(attribute_id=4, attribute_name="current_debit_amount"),
        5: AttributeDescription(attribute_id=5, attribute_name="credit_in_use"),
        6: AttributeDescription(attribute_id=6, attribute_name="available_credit"),
        7: AttributeDescription(attribute_id=7, attribute_name="emergency_credit_limit"),
        8: AttributeDescription(attribute_id=8, attribute_name="emergency_credit_threshold"),
        9: AttributeDescription(attribute_id=9, attribute_name="emergency_credit_status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset account to defaults."""
        self.account_status = 0
        self.current_credit_amount = 0.0
        self.current_debit_amount = 0.0
        self.credit_in_use = 0.0
        self.available_credit = 0.0
        self.emergency_credit_status = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def has_sufficient_credit(self, amount: float) -> bool:
        """Check if account has sufficient credit."""
        return self.available_credit >= amount

    def use_credit(self, amount: float) -> bool:
        """Use credit from account."""
        if self.has_sufficient_credit(amount):
            self.available_credit -= amount
            self.credit_in_use += amount
            return True
        return False
