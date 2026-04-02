"""IC class 24 - Infrared Setup (IEC Twisted Pair Setup).

Configuration for infrared optical communication port.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class InfraredSetup:
    """COSEM IC Infrared Setup (class_id=24).

    Attributes:
        1: logical_name (static)
        2: baudrate (static)
        3: parity (static)
        4: stop_bits (static)
        5: data_bits (static)
        6: protocol_type (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_TWISTED_PAIR_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    baudrate: int = 9600
    parity: int = 2
    stop_bits: int = 1
    data_bits: int = 8
    protocol_type: int = 1  # HDLC

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="baudrate"),
        3: AttributeDescription(attribute_id=3, attribute_name="parity"),
        4: AttributeDescription(attribute_id=4, attribute_name="stop_bits"),
        5: AttributeDescription(attribute_id=5, attribute_name="data_bits"),
        6: AttributeDescription(attribute_id=6, attribute_name="protocol_type"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
