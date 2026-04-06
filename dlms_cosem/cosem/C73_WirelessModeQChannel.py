"""IC class 73 - WirelessModeQChannel.

Wireless Mode Q Channel - wireless M-Bus mode Q channel configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=73
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class WirelessModeQChannel:
    """COSEM IC WirelessModeQChannel (class_id=73).

    Attributes:
        1: logical_name (static)
        2: channel_info (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_WIRELESS_MODE_Q_CHANNEL
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    channel_info: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'channel_info'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

