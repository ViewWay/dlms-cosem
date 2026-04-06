"""IC class 51 - SFSKActiveInitiator.

S-FSK Active Initiator - manages S-FSK active initiator.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=51
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SFSKActiveInitiator:
    """COSEM IC SFSKActiveInitiator (class_id=51).

    Attributes:
        1: logical_name (static)
        2: active_initiator (dynamic)
        3: active_initiator_count (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_ACTIVE_INITIATOR
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    active_initiator: List[Any] = attr.ib(factory=list)
    active_initiator_count: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'active_initiator', 3: 'active_initiator_count'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

