"""IC class 53 - SFSKMACCounters.

S-FSK MAC Counters - S-FSK MAC layer counters.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=53
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SFSKMACCounters:
    """COSEM IC SFSKMACCounters (class_id=53).

    Attributes:
        1: logical_name (static)
        2: tx_packet_count (dynamic)
        3: rx_packet_count (dynamic)
        4: crc_error_count (dynamic)
        5: tx_time (dynamic)
        6: rx_time (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_MAC_COUNTERS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    tx_packet_count: Optional[int] = 0
    rx_packet_count: Optional[int] = 0
    crc_error_count: Optional[int] = 0
    tx_time: Optional[int] = 0
    rx_time: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'tx_packet_count', 3: 'rx_packet_count', 4: 'crc_error_count', 5: 'tx_time', 6: 'rx_time'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

