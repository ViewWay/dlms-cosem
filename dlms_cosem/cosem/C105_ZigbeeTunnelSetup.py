"""IC class 105 - ZigbeeTunnelSetup.

ZigBee Tunnel Setup - ZigBee tunnel configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=105
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ZigbeeTunnelSetup:
    """COSEM IC ZigbeeTunnelSetup (class_id=105).

    Attributes:
        1: logical_name (static)
        2: tunnel_address (dynamic)
        3: tunnel_port (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_TUNNEL_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    tunnel_address: Optional[bytes] = None
    tunnel_port: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'tunnel_address', 3: 'tunnel_port'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

