"""IC class 133 - IEC14908Diagnostic.

ISO/IEC 14908 Diagnostic - PLC diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=133
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC14908Diagnostic:
    """COSEM IC IEC14908Diagnostic (class_id=133).

    Attributes:
        1: logical_name (static)
        2: messages_sent (dynamic)
        3: messages_received (dynamic)
        4: messages_failed (dynamic)
        5: crc_errors (dynamic)
        6: timeouts (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_14908_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    messages_sent: Optional[int] = 0
    messages_received: Optional[int] = 0
    messages_failed: Optional[int] = 0
    crc_errors: Optional[int] = 0
    timeouts: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'messages_sent', 3: 'messages_received', 4: 'messages_failed', 5: 'crc_errors', 6: 'timeouts'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

