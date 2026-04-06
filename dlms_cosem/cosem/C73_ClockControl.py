"""IC class 73 - Clock Control.

Controls the clock, including time adjustments and synchronisation.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: enable (static, boolean)
    3: clock_base (static)
    4: clock_status (static)
    5: next_time_adjustment (static)
    6: adjust_clock (method)
"""
from typing import Any, ClassVar, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ClockControl:
    """COSEM IC Clock Control (class_id=73).

    Attributes:
        1: logical_name (static)
        2: enable (static, boolean)
        3: clock_base (static)
        4: clock_status (static)
        5: next_time_adjustment (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.CLOCK_CONTROL
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    enable: bool = False
    clock_base: Optional[Any] = None
    clock_status: int = 0
    next_time_adjustment: Optional[Any] = None
