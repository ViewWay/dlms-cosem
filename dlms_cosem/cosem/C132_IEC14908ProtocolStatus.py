"""IC class 132 - IEC14908ProtocolStatus.

ISO/IEC 14908 Protocol Status - PLC protocol status.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=132
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC14908ProtocolStatus:
    """COSEM IC IEC14908ProtocolStatus (class_id=132).

    Attributes:
        1: logical_name (static)
        2: protocol_status (dynamic)
        3: connection_status (dynamic)
        4: communication_statistics (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_14908_PROTOCOL_STATUS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    protocol_status: Optional[int] = 0
    connection_status: Optional[int] = 0
    communication_statistics: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'protocol_status', 3: 'connection_status', 4: 'communication_statistics'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

