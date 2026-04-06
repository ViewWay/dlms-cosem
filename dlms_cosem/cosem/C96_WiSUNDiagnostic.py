"""IC class 96 - WiSUNDiagnostic.

Wi-SUN Diagnostic - Wi-SUN network diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=96
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class WiSUNDiagnostic:
    """COSEM IC WiSUNDiagnostic (class_id=96).

    Attributes:
        1: logical_name (static)
        2: messages_sent (dynamic)
        3: messages_received (dynamic)
        4: messages_failed (dynamic)
        5: messages_retransmitted (dynamic)
        6: phy_tx_total (dynamic)
        7: phy_rx_total (dynamic)
        8: phy_tx_error (dynamic)
        9: phy_rx_error (dynamic)
        10: mac_tx_total (dynamic)
        11: mac_rx_total (dynamic)
        12: mac_tx_error (dynamic)
        13: mac_rx_error (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.WISUN_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    messages_sent: Optional[int] = 0
    messages_received: Optional[int] = 0
    messages_failed: Optional[int] = 0
    messages_retransmitted: Optional[int] = 0
    phy_tx_total: Optional[int] = 0
    phy_rx_total: Optional[int] = 0
    phy_tx_error: Optional[int] = 0
    phy_rx_error: Optional[int] = 0
    mac_tx_total: Optional[int] = 0
    mac_rx_total: Optional[int] = 0
    mac_tx_error: Optional[int] = 0
    mac_rx_error: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'messages_sent', 3: 'messages_received', 4: 'messages_failed', 5: 'messages_retransmitted', 6: 'phy_tx_total', 7: 'phy_rx_total', 8: 'phy_tx_error', 9: 'phy_rx_error', 10: 'mac_tx_total', 11: 'mac_rx_total', 12: 'mac_tx_error', 13: 'mac_rx_error'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

