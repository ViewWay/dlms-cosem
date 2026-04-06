"""IC class 29 - AutoConnect.

Auto Connect - manages automatic connection establishment.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=29
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class AutoConnect:
    """COSEM IC AutoConnect (class_id=29).

    Attributes:
        1: logical_name (static)
        2: mode (dynamic)
        3: repetitions (dynamic)
        4: repetition_delay (dynamic)
        5: calling_window (dynamic)
        6: allowed_destinations (dynamic)
    Methods:
        1: set_mode
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.AUTO_CONNECT  # class_id=29
    VERSION: ClassVar[int] = 2

    logical_name: Obis
    mode: Optional[int] = 0
    repetitions: Optional[int] = 0
    repetition_delay: Optional[int] = 0
    calling_window: List[Any] = attr.ib(factory=list)
    allowed_destinations: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mode', 3: 'repetitions', 4: 'repetition_delay', 5: 'calling_window', 6: 'allowed_destinations'}
    METHODS: ClassVar[Dict[int, str]] = {1: 'set_mode'}

    def set_mode(self) -> None:
        """Method 1: set_mode."""

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

