"""IC class 43 - MAC Address Setup.

MAC address configuration for network devices.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.3
"""
from typing import ClassVar, Dict, Optional, Tuple

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class MACAddressSetup:
    """COSEM IC MAC Address Setup (class_id=43).

    Attributes:
        1: logical_name (static)
        2: mac_address (dynamic) - MAC address as 6-tuple
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MAC_ADDRESS_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mac_address: Tuple[int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="mac_address"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset MAC address to default."""
        self.mac_address = (0, 0, 0, 0, 0, 0)

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def get_mac_string(self) -> str:
        """Get MAC address as colon-separated string."""
        return ":".join(f"{b:02X}" for b in self.mac_address)

    def set_mac_from_string(self, mac_str: str) -> None:
        """Set MAC address from colon-separated string."""
        parts = mac_str.split(":")
        if len(parts) == 6:
            self.mac_address = tuple(int(p, 16) for p in parts)
