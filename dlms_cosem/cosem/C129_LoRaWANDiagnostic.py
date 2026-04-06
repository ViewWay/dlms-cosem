"""IC class 129 - LoRaWANDiagnostic.

LoRaWAN Diagnostic - LoRaWAN network diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=129
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LoRaWANDiagnostic:
    """COSEM IC LoRaWANDiagnostic (class_id=129).

    Attributes:
        1: logical_name (static)
        2: messages_sent (dynamic)
        3: messages_received (dynamic)
        4: messages_failed (dynamic)
        5: messages_retransmitted (dynamic)
        6: lorawan_rssi (dynamic)
        7: lorawan_snr (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LORAWAN_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    messages_sent: Optional[int] = 0
    messages_received: Optional[int] = 0
    messages_failed: Optional[int] = 0
    messages_retransmitted: Optional[int] = 0
    lorawan_rssi: Optional[int] = 0
    lorawan_snr: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'messages_sent', 3: 'messages_received', 4: 'messages_failed', 5: 'messages_retransmitted', 6: 'lorawan_rssi', 7: 'lorawan_snr'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

