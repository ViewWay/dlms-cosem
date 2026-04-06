"""IC class 19 - Local Port Setup (LP Setup).

Configuration for the local port (optical/IEC 62056-21).

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class LocalPortSetup:
    """COSEM IC Local Port Setup (class_id=19).

    Attributes:
        1: logical_name (static)
        2: default_mode (static) - 1=HDLC, 2=wrapper, 3=other
        3: default_baudrate (static)
        4: proposed_baudrate (static)
        5: response_time (static) - ms
        6: device_address (static)
        7: password (static) - LLS password
        8: repeat_count (static)
    Methods:
        1: change_baudrate
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_LOCAL_PORT_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    default_mode: int = 1
    default_baudrate: int = 300
    proposed_baudrate: int = 9600
    response_time: int = 500
    device_address: bytes = b"\x00\x00\x00\x00"
    password: Optional[bytes] = None
    repeat_count: int = 3

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="default_mode"),
        3: AttributeDescription(attribute_id=3, attribute_name="default_baudrate"),
        4: AttributeDescription(attribute_id=4, attribute_name="proposed_baudrate"),
        5: AttributeDescription(attribute_id=5, attribute_name="response_time"),
        6: AttributeDescription(attribute_id=6, attribute_name="device_address"),
        7: AttributeDescription(attribute_id=7, attribute_name="password"),
        8: AttributeDescription(attribute_id=8, attribute_name="repeat_count"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "change_baudrate"}

    def change_baudrate(self, baudrate: int) -> None:
        self.proposed_baudrate = baudrate

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
