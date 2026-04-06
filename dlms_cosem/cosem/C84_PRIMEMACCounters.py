"""IC class 84 - PRIMEMACCounters.

PRIME NB OFDM PLC MAC Counters - PRIME MAC counters.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=84
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMEMACCounters:
    """COSEM IC PRIMEMACCounters (class_id=84).

    Attributes:
        1: logical_name (static)
        2: mac_tx_total (dynamic)
        3: mac_rx_total (dynamic)
        4: mac_tx_error (dynamic)
        5: mac_rx_error (dynamic)
        6: mac_tx_dropped (dynamic)
        7: mac_rx_dropped (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_OFDM_PLC_MAC_COUNTERS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mac_tx_total: Optional[int] = 0
    mac_rx_total: Optional[int] = 0
    mac_tx_error: Optional[int] = 0
    mac_rx_error: Optional[int] = 0
    mac_tx_dropped: Optional[int] = 0
    mac_rx_dropped: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mac_tx_total', 3: 'mac_rx_total', 4: 'mac_tx_error', 5: 'mac_rx_error', 6: 'mac_tx_dropped', 7: 'mac_rx_dropped'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

