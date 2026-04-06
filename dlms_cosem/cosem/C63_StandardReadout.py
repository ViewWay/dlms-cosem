"""IC class 63 - Standard Readout.

Standard data readout for bulk meter reading operations.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: capture_objects (static)
    3: capture_period (static)
    4: last_capture_time (dynamic)
    5: sort_method (static)
    6: sort_object (static)
    7: capture_buffer (dynamic)
    8: profile_entries (dynamic)
    9: profile_status (dynamic)
"""
from typing import Any, ClassVar, List, Optional, Tuple

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.capture_object import CaptureObject


@attr.s(auto_attribs=True)
class StandardReadout:
    """COSEM IC Standard Readout (class_id=63).

    Attributes:
        1: logical_name (static)
        2: capture_objects (static)
        3: capture_period (static)
        4: last_capture_time (dynamic)
        7: capture_buffer (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.STANDARD_READOUT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    capture_objects: List[CaptureObject] = attr.ib(factory=list)
    capture_period: int = 0
    last_capture_time: Optional[Any] = None
    buffer: List[List] = attr.ib(factory=list)
