"""IC class 131 - IEC14908ProtocolSetup.

ISO/IEC 14908 Protocol Setup - PLC protocol configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=131
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC14908ProtocolSetup:
    """COSEM IC IEC14908ProtocolSetup (class_id=131).

    Attributes:
        1: logical_name (static)
        2: protocol_mode (dynamic)
        3: protocol_version (dynamic)
        4: protocol_parameters (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_14908_PROTOCOL_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    protocol_mode: Optional[int] = 0
    protocol_version: Optional[int] = 0
    protocol_parameters: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'protocol_mode', 3: 'protocol_version', 4: 'protocol_parameters'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

