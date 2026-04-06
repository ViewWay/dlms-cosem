"""IC class 37 - Multiplier.

Applies a multiplier (and optionally offset) to register values.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: multiplier (static, long)
    3: offset (static, long)
    4: deviation (static, long)
"""
from typing import ClassVar

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class Multiplier:
    """COSEM IC Multiplier (class_id=37).

    Attributes:
        1: logical_name (static)
        2: multiplier (static)
        3: offset (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MULTIPLIER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    multiplier: float = 1.0
    offset: float = 0.0
