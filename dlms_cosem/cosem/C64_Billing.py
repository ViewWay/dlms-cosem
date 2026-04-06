"""IC class 64 - Billing.

Billing / payment metering for prepayment and credit management.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: charging_date_time (dynamic)
    3: billing_period (static)
    4: billing_cycle (static)
    5: last_billing_date_time (dynamic)
    6: amount_prescribed (dynamic)
    7: amount_to_be_paid (dynamic)
    8: debt_amount (dynamic)
    9: credit_amount (dynamic)
    10: charge_type (static)
"""
from typing import Any, ClassVar, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class Billing:
    """COSEM IC Billing (class_id=64).

    Attributes:
        1: logical_name (static)
        2: charging_date_time (dynamic)
        3: billing_period (static)
        4: billing_cycle (static)
        5: last_billing_date_time (dynamic)
        6: amount_prescribed (dynamic)
        7: amount_to_be_paid (dynamic)
        8: debt_amount (dynamic)
        9: credit_amount (dynamic)
        10: charge_type (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.BILLING
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    charging_datetime: Optional[Any] = None
    billing_period: int = 0
    billing_cycle: int = 0
    last_billing_datetime: Optional[Any] = None
    amount_prescribed: int = 0
    amount_to_be_paid: int = 0
    debt_amount: int = 0
    credit_amount: int = 0
    charge_type: int = 0
