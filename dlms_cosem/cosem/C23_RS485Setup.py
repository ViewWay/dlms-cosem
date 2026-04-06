"""IC class 23 - RS485 Setup (IEC HDLC Setup).

Configuration for RS485 communication port.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class RS485Setup:
    """COSEM IC RS485 Setup (class_id=23).

    Attributes:
        1: logical_name (static)
        2: default_baudrate (static)
        3: proposed_baudrate (static)
        4: address (static)
        5: parity (static) - 0=none, 1=odd, 2=even
        6: stop_bits (static) - 1 or 2
        7: data_bits (static) - 7 or 8
        8: mode (static) - HDLC mode settings
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_HDLC_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    default_baudrate: int = 9600
    proposed_baudrate: int = 9600
    address: int = 1
    parity: int = 2  # even
    stop_bits: int = 1
    data_bits: int = 8
    mode: int = 1

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="default_baudrate"),
        3: AttributeDescription(attribute_id=3, attribute_name="proposed_baudrate"),
        4: AttributeDescription(attribute_id=4, attribute_name="address"),
        5: AttributeDescription(attribute_id=5, attribute_name="parity"),
        6: AttributeDescription(attribute_id=6, attribute_name="stop_bits"),
        7: AttributeDescription(attribute_id=7, attribute_name="data_bits"),
        8: AttributeDescription(attribute_id=8, attribute_name="mode"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
