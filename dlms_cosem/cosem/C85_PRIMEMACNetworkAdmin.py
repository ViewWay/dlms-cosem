"""IC class 85 - PRIMEMACNetworkAdmin.

PRIME NB OFDM PLC MAC Network Administration Data - PRIME network admin.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=85
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMEMACNetworkAdmin:
    """COSEM IC PRIMEMACNetworkAdmin (class_id=85).

    Attributes:
        1: logical_name (static)
        2: network_id (dynamic)
        3: network_role (dynamic)
        4: network_state (dynamic)
        5: network_device_list (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_OFDM_PLC_MAC_NETWORK_ADMINISTRATION_DATA
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    network_id: Optional[int] = 0
    network_role: Optional[int] = 0
    network_state: Optional[int] = 0
    network_device_list: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'network_id', 3: 'network_role', 4: 'network_state', 5: 'network_device_list'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

