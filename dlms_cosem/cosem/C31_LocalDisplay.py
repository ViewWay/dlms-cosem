"""IC class 31 - Local Display.

Controls the local display of the meter.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: display_data (static)
    3: info_to_display (static)
    4: entry_display_time (static)
    5: interval_display_time (static)
"""
from typing import ClassVar, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LocalDisplay:
    """COSEM IC Local Display (class_id=31).

    Attributes:
        1: logical_name (static)
        2: display_data (static)
        3: info_to_display (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LOCAL_DISPLAY
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    display_data: Optional[List] = None
    info_to_display: Optional[List] = None
