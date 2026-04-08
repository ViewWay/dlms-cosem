"""IC110 - ZigBee Setup.

Configuration for ZigBee wireless communication module in smart meters.
Includes network parameters, security, and neighbor info.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ZigBeeSetup:
    """COSEM IC ZigBee Setup (class_id=110).

    Attributes:
        1: logical_name (static)
        2: network_pan_id (static, uint16)
        3: network_channel (static, uint8)
        4: short_address (static, uint16)
        5: extended_address (static, octet-string EUI-64)
        6: network_key (static, octet-string)
        7: trust_center_key (static, octet-string)
        8: status (dynamic, enum)
        9: signal_quality (dynamic, int, LQI)
    Methods:
        1: join_network
        2: leave_network
        3: reset_network
    """

    CLASS_ID: ClassVar[int] = 110
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    network_pan_id: int = 0
    network_channel: int = 0
    short_address: int = 0xFFFF  # not assigned
    extended_address: bytes = b"\x00" * 8
    network_key: bytes = b"\x00" * 16
    trust_center_key: bytes = b"\x00" * 16
    status: int = 0  # 0=offline, 1=joining, 2=joined, 3=coordinator
    signal_quality: int = 0  # LQI (0-255)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="network_pan_id"),
        3: AttributeDescription(attribute_id=3, attribute_name="network_channel"),
        4: AttributeDescription(attribute_id=4, attribute_name="short_address"),
        5: AttributeDescription(attribute_id=5, attribute_name="extended_address"),
        6: AttributeDescription(attribute_id=6, attribute_name="network_key"),
        7: AttributeDescription(attribute_id=7, attribute_name="trust_center_key"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        8: AttributeDescription(attribute_id=8, attribute_name="status"),
        9: AttributeDescription(attribute_id=9, attribute_name="signal_quality"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "join_network", 2: "leave_network", 3: "reset_network"
    }

    def join_network(self) -> None:
        self.status = 1  # joining

    def leave_network(self) -> None:
        self.status = 0

    def reset_network(self) -> None:
        self.status = 0
        self.short_address = 0xFFFF

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
