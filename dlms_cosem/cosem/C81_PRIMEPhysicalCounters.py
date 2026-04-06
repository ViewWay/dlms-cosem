"""IC class 81 - PRIMEPhysicalCounters.

PRIME NB OFDM PLC Physical Layer Counters - PRIME PHY counters.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=81
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMEPhysicalCounters:
    """COSEM IC PRIMEPhysicalCounters (class_id=81).

    Attributes:
        1: logical_name (static)
        2: phy_tx_drop (dynamic)
        3: phy_rx_total (dynamic)
        4: phy_rx_crc_error (dynamic)
        5: phy_tx_total (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_OFDM_PLC_PHYSICAL_LAYER_COUNTERS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    phy_tx_drop: Optional[int] = 0
    phy_rx_total: Optional[int] = 0
    phy_rx_crc_error: Optional[int] = 0
    phy_tx_total: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'phy_tx_drop', 3: 'phy_rx_total', 4: 'phy_rx_crc_error', 5: 'phy_tx_total'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

