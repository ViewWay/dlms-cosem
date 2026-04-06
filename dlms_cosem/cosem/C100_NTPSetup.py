"""IC class 100 - NTP Setup.

NTP (Network Time Protocol) configuration.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.9
"""
from typing import ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class NTPSetup:
    """COSEM IC NTP Setup (class_id=100).

    Attributes:
        1: logical_name (static)
        2: ntp_servers (dynamic) - List of NTP server addresses
        3: ntp_port (dynamic) - NTP port number
        4: ntp_poll_interval (dynamic) - Polling interval in seconds
        5: ntp_enabled (dynamic) - Whether NTP is enabled
        6: ntp_time_offset (dynamic) - Time offset from NTP server
        7: ntp_last_sync (dynamic) - Last successful sync time
    Methods:
        1: reset
        2: sync_now
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.NTP_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    ntp_servers: List[str] = attr.ib(factory=list)
    ntp_port: int = 123
    ntp_poll_interval: int = 3600
    ntp_enabled: bool = False
    ntp_time_offset: int = 0
    ntp_last_sync: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="ntp_servers"),
        3: AttributeDescription(attribute_id=3, attribute_name="ntp_port"),
        4: AttributeDescription(attribute_id=4, attribute_name="ntp_poll_interval"),
        5: AttributeDescription(attribute_id=5, attribute_name="ntp_enabled"),
        6: AttributeDescription(attribute_id=6, attribute_name="ntp_time_offset"),
        7: AttributeDescription(attribute_id=7, attribute_name="ntp_last_sync"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "sync_now",
    }

    def reset(self) -> None:
        """Method 1: Reset NTP configuration."""
        self.ntp_servers = []
        self.ntp_enabled = False
        self.ntp_time_offset = 0
        self.ntp_last_sync = None

    def sync_now(self) -> None:
        """Method 2: Trigger immediate NTP sync."""
        # In real implementation, would trigger NTP synchronization
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def add_server(self, server_address: str) -> None:
        """Add an NTP server."""
        self.ntp_servers.append(server_address)
