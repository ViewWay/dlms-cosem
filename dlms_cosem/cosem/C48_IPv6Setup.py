"""IC class 48 - IPv6Setup.

IPv6 Setup - IPv6 address configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=48
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IPv6Setup:
    """COSEM IC IPv6Setup (class_id=48).

    Attributes:
        1: logical_name (static)
        2: address_configuration_mode (dynamic)
        3: link_local_address (dynamic)
        4: address_list (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IPV6_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    address_configuration_mode: Optional[int] = 0
    link_local_address: Optional[bytes] = None
    address_list: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'address_configuration_mode', 3: 'link_local_address', 4: 'address_list'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

