"""IC class 207 - Total.

Generic accumulator / total value counter.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: value (dynamic, any)
    3: scaler_unit (static, structure)
    4: status (dynamic, double-long-unsigned)
"""
from typing import Any, ClassVar, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class Total:
    """COSEM IC Total (class_id=207).

    Attributes:
        1: logical_name (static)
        2: value (dynamic)
        3: scaler_unit (static)
        4: status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.TOTAL
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value: Any = None
    unit: int = 0
    scaler: int = 0
    status: int = 0
