"""IC109 - TCP/UDP Setup.

Configuration for TCP/UDP socket connections used by the meter's
communication module (e.g., for connecting to head-end system).

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class TcpUdpSetup:
    """COSEM IC TCP/UDP Setup (class_id=109).

    Attributes:
        1: logical_name (static)
        2: protocol_type (static, enum: 0=TCP, 1=UDP)
        3: remote_ip (static, string)
        4: remote_port (static, uint16)
        5: local_port (static, uint16)
        6: connection_timeout (static, uint16, seconds)
        7: inactivity_timeout (static, uint16, seconds)
        8: status (dynamic, enum)
        9: retry_count (static)
    Methods:
        1: connect
        2: disconnect
    """

    CLASS_ID: ClassVar[int] = 109
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    protocol_type: int = 0  # TCP
    remote_ip: str = ""
    remote_port: int = 4059
    local_port: int = 0
    connection_timeout: int = 30
    inactivity_timeout: int = 120
    status: int = 0  # 0=disconnected, 1=connecting, 2=connected, 3=error
    retry_count: int = 3

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="protocol_type"),
        3: AttributeDescription(attribute_id=3, attribute_name="remote_ip"),
        4: AttributeDescription(attribute_id=4, attribute_name="remote_port"),
        5: AttributeDescription(attribute_id=5, attribute_name="local_port"),
        6: AttributeDescription(attribute_id=6, attribute_name="connection_timeout"),
        7: AttributeDescription(attribute_id=7, attribute_name="inactivity_timeout"),
        9: AttributeDescription(attribute_id=9, attribute_name="retry_count"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        8: AttributeDescription(attribute_id=8, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "connect", 2: "disconnect"}

    def connect(self) -> None:
        self.status = 2

    def disconnect(self) -> None:
        self.status = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
