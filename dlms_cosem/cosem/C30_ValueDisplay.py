"""IC class 30 - Value Display.

Displays a value on a local display.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: value_to_display (dynamic)
    3: status (dynamic)
"""
from typing import Any, ClassVar, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ValueDisplay:
    """COSEM IC Value Display (class_id=30).

    Attributes:
        1: logical_name (static)
        2: value_to_display (dynamic)
        3: status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.VALUE_DISPLAY
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value_to_display: Any = None
    status: int = 0
