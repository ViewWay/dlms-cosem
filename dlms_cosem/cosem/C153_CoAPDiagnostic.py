"""IC class 153 - CoAPDiagnostic.

CoAP Diagnostic - Constrained Application Protocol diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=153
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class CoAPDiagnostic:
    """COSEM IC CoAPDiagnostic (class_id=153).

    Attributes:
        1: logical_name (static)
        2: messages_sent (dynamic)
        3: messages_received (dynamic)
        4: messages_failed (dynamic)
        5: messages_retransmitted (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.COAP_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    messages_sent: Optional[int] = 0
    messages_received: Optional[int] = 0
    messages_failed: Optional[int] = 0
    messages_retransmitted: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'messages_sent', 3: 'messages_received', 4: 'messages_failed', 5: 'messages_retransmitted'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

