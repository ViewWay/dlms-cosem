"""IC class 45 - GPRS Modem Setup.

GPRS modem configuration for smart meters.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.4
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class GPRSSetup:
    """COSEM IC GPRS Modem Setup (class_id=45).

    Attributes:
        1: logical_name (static)
        2: apn (dynamic) - Access Point Name
        3: pin_code (dynamic) - SIM PIN code
        4: username (dynamic) - Authentication username
        5: password (dynamic) - Authentication password
        6: quality_of_service (dynamic) - QoS settings
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.GPRS_MODEM_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    apn: str = ""
    pin_code: str = ""
    username: str = ""
    password: str = ""
    quality_of_service: Optional[Dict[str, Any]] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="apn"),
        3: AttributeDescription(attribute_id=3, attribute_name="pin_code"),
        4: AttributeDescription(attribute_id=4, attribute_name="username"),
        5: AttributeDescription(attribute_id=5, attribute_name="password"),
        6: AttributeDescription(attribute_id=6, attribute_name="quality_of_service"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset GPRS configuration to defaults."""
        self.apn = ""
        self.pin_code = ""
        self.username = ""
        self.password = ""
        self.quality_of_service = None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES


# Alias for backward compatibility with existing code
GprsModemSetup = GPRSSetup
