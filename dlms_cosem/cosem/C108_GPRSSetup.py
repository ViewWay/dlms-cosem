"""IC108 - GPRS Setup.

Configuration for GPRS (2G/3G/4G) communication module in smart meters.
Includes APN, authentication, and connection parameters.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class GPRSSetup:
    """COSEM IC GPRS Setup (class_id=108).

    Attributes:
        1: logical_name (static)
        2: apn (static, string)
        3: pin_code (static, octet-string)
        4: user_name (static, string)
        5: password (static, octet-string)
        6: connection_type (static, enum: 0=CSD, 1=GPRS)
        7: status (dynamic, enum)
        8: signal_strength (dynamic, int, dBm)
    Methods:
        1: connect
        2: disconnect
    """

    CLASS_ID: ClassVar[int] = 108
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    apn: str = "internet"
    pin_code: str = ""
    user_name: str = ""
    password: str = ""
    connection_type: int = 1  # GPRS
    status: int = 0  # 0=disconnected, 1=connecting, 2=connected
    signal_strength: int = 0  # dBm

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="apn"),
        3: AttributeDescription(attribute_id=3, attribute_name="pin_code"),
        4: AttributeDescription(attribute_id=4, attribute_name="user_name"),
        5: AttributeDescription(attribute_id=5, attribute_name="password"),
        6: AttributeDescription(attribute_id=6, attribute_name="connection_type"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        7: AttributeDescription(attribute_id=7, attribute_name="status"),
        8: AttributeDescription(attribute_id=8, attribute_name="signal_strength"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "connect", 2: "disconnect"}

    def connect(self) -> None:
        self.status = 2

    def disconnect(self) -> None:
        self.status = 0

    def is_connected(self) -> bool:
        return self.status == 2

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
