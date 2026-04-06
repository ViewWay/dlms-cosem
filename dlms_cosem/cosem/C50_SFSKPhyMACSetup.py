"""IC class 50 - SFSKPhyMACSetup.

S-FSK Phy&MAC Setup - S-FSK physical and MAC layer configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=50
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SFSKPhyMACSetup:
    """COSEM IC SFSKPhyMACSetup (class_id=50).

    Attributes:
        1: logical_name (static)
        2: mac_address (dynamic)
        3: phy_list (dynamic)
        4: tx_level (dynamic)
        5: rx_level (dynamic)
        6: frequency_band (dynamic)
        7: data_rate (dynamic)
        8: tx_frequency (dynamic)
        9: rx_frequency (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_PHY_MAC_SETUP
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    mac_address: Optional[bytes] = None
    phy_list: List[Any] = attr.ib(factory=list)
    tx_level: Optional[int] = 0
    rx_level: Optional[int] = 0
    frequency_band: Optional[int] = 0
    data_rate: Optional[int] = 0
    tx_frequency: Optional[int] = 0
    rx_frequency: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mac_address', 3: 'phy_list', 4: 'tx_level', 5: 'rx_level', 6: 'frequency_band', 7: 'data_rate', 8: 'tx_frequency', 9: 'rx_frequency'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

