"""IC class 44 - PPP Setup.

PPP (Point-to-Point Protocol) configuration.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.5
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


class PPPAuthProtocol:
    """PPP authentication protocols."""
    NONE = 0
    PAP = 1
    CHAP = 2


@attr.s(auto_attribs=True)
class PPPSetup:
    """COSEM IC PPP Setup (class_id=44).

    Attributes:
        1: logical_name (static)
        2: username (dynamic) - PPP username
        3: password (dynamic) - PPP password
        4: authentication_protocol (dynamic) - Auth protocol (PAP/CHAP)
        5: idle_timeout (dynamic) - Idle timeout in seconds
        6: local_ip (dynamic) - Local IP address
        7: remote_ip (dynamic) - Remote IP address
        8: dns_primary (dynamic) - Primary DNS server
        9: dns_secondary (dynamic) - Secondary DNS server
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PPP_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    username: str = ""
    password: str = ""
    authentication_protocol: int = PPPAuthProtocol.NONE
    idle_timeout: int = 0
    local_ip: str = "0.0.0.0"
    remote_ip: str = "0.0.0.0"
    dns_primary: str = "0.0.0.0"
    dns_secondary: str = "0.0.0.0"

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="username"),
        3: AttributeDescription(attribute_id=3, attribute_name="password"),
        4: AttributeDescription(attribute_id=4, attribute_name="authentication_protocol"),
        5: AttributeDescription(attribute_id=5, attribute_name="idle_timeout"),
        6: AttributeDescription(attribute_id=6, attribute_name="local_ip"),
        7: AttributeDescription(attribute_id=7, attribute_name="remote_ip"),
        8: AttributeDescription(attribute_id=8, attribute_name="dns_primary"),
        9: AttributeDescription(attribute_id=9, attribute_name="dns_secondary"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset PPP configuration to defaults."""
        self.username = ""
        self.password = ""
        self.authentication_protocol = PPPAuthProtocol.NONE
        self.idle_timeout = 0
        self.local_ip = "0.0.0.0"
        self.remote_ip = "0.0.0.0"
        self.dns_primary = "0.0.0.0"
        self.dns_secondary = "0.0.0.0"

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
