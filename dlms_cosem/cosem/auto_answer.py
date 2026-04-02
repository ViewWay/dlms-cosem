"""IC class 28 - Auto Answer.

Controls automatic answering for modem-based connections.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class AutoAnswer:
    """COSEM IC Auto Answer (class_id=28).

    Attributes:
        1: logical_name (static)
        2: mode (static) - 0=disabled, 1=enabled
        3: ringing_pattern (static)
        4: number_of_rings (static)
        5: listening_window (static) - list of CosemDateTime
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.AUTO_ANSWER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mode: int = 1
    ringing_pattern: Optional[str] = None
    number_of_rings: int = 3
    listening_window: list = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="mode"),
        3: AttributeDescription(attribute_id=3, attribute_name="ringing_pattern"),
        4: AttributeDescription(attribute_id=4, attribute_name="number_of_rings"),
        5: AttributeDescription(attribute_id=5, attribute_name="listening_window"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
