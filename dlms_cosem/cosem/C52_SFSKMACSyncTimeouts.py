"""IC class 52 - SFSKMACSyncTimeouts.

S-FSK MAC Synchronization Timeouts - S-FSK MAC sync timeout configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=52
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SFSKMACSyncTimeouts:
    """COSEM IC SFSKMACSyncTimeouts (class_id=52).

    Attributes:
        1: logical_name (static)
        2: time_outs (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_MAC_SYNCHRONISATION_TIMEOUTS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    time_outs: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'time_outs'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

