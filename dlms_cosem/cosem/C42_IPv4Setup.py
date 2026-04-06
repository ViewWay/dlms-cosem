"""IC class 42 - IPv4 Setup.

IPv4 network configuration for smart meters and IoT devices.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.2
"""
from typing import ClassVar, Dict, Optional, Tuple

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class IPv4Setup:
    """COSEM IC IPv4 Setup (class_id=42).

    Attributes:
        1: logical_name (static)
        2: ip_address (dynamic) - IPv4 address as 4-tuple
        3: subnet_mask (dynamic) - Subnet mask as 4-tuple
        4: gateway (dynamic) - Gateway address as 4-tuple
        5: primary_dns (dynamic) - Primary DNS as 4-tuple
        6: secondary_dns (dynamic) - Secondary DNS as 4-tuple
        7: dhcp_enabled (dynamic) - Whether DHCP is enabled
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IPV4_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    ip_address: Tuple[int, int, int, int] = (0, 0, 0, 0)
    subnet_mask: Tuple[int, int, int, int] = (255, 255, 255, 0)
    gateway: Tuple[int, int, int, int] = (0, 0, 0, 0)
    primary_dns: Tuple[int, int, int, int] = (0, 0, 0, 0)
    secondary_dns: Tuple[int, int, int, int] = (0, 0, 0, 0)
    dhcp_enabled: bool = False

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="ip_address"),
        3: AttributeDescription(attribute_id=3, attribute_name="subnet_mask"),
        4: AttributeDescription(attribute_id=4, attribute_name="gateway"),
        5: AttributeDescription(attribute_id=5, attribute_name="primary_dns"),
        6: AttributeDescription(attribute_id=6, attribute_name="secondary_dns"),
        7: AttributeDescription(attribute_id=7, attribute_name="dhcp_enabled"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset all IPv4 configuration to defaults."""
        self.ip_address = (0, 0, 0, 0)
        self.subnet_mask = (255, 255, 255, 0)
        self.gateway = (0, 0, 0, 0)
        self.primary_dns = (0, 0, 0, 0)
        self.secondary_dns = (0, 0, 0, 0)
        self.dhcp_enabled = False

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def get_ip_string(self) -> str:
        """Get IP address as dotted string."""
        return ".".join(str(b) for b in self.ip_address)

    def get_subnet_string(self) -> str:
        """Get subnet mask as dotted string."""
        return ".".join(str(b) for b in self.subnet_mask)
