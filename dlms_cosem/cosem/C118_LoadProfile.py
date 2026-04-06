"""IC class 118 - Load Profile.

Load profile for electricity metering data collection.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: capture_objects (static)
    3: capture_period (static)
    4: sort_method (static)
    5: sort_object (static)
    6: capture_buffer (dynamic)
    7: profile_entries (dynamic)
    8: profile_status (dynamic)
"""
from typing import Any, ClassVar, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.capture_object import CaptureObject


@attr.s(auto_attribs=True)
class LoadProfile:
    """COSEM IC Load Profile (class_id=118).

    Attributes:
        1: logical_name (static)
        2: capture_objects (static)
        3: capture_period (static)
        6: capture_buffer (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LOAD_PROFILE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    capture_objects: List[CaptureObject] = attr.ib(factory=list)
    capture_period: int = 0
    buffer: List[List] = attr.ib(factory=list)
