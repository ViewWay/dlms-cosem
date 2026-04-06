"""IC class 90 - G3MACCounters.

G3-PLC MAC Layer Counters - G3-PLC MAC layer counters.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=90
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class G3MACCounters:
    """COSEM IC G3MACCounters (class_id=90).

    Attributes:
        1: logical_name (static)
        2: mac_tx_packet_count (dynamic)
        3: mac_rx_packet_count (dynamic)
        4: mac_crc_error_count (dynamic)
        5: mac_tx_time (dynamic)
        6: mac_rx_time (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.G3_PLC_MAC_LAYER_COUNTERS
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    mac_tx_packet_count: Optional[int] = 0
    mac_rx_packet_count: Optional[int] = 0
    mac_crc_error_count: Optional[int] = 0
    mac_tx_time: Optional[int] = 0
    mac_rx_time: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mac_tx_packet_count', 3: 'mac_rx_packet_count', 4: 'mac_crc_error_count', 5: 'mac_tx_time', 6: 'mac_rx_time'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

