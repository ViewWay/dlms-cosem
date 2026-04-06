"""IC class 57 - LLCType1Setup.

IEC 8802-2 LLC Type 1 Setup - LLC Type 1 connectionless setup.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=57
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LLCType1Setup:
    """COSEM IC LLCType1Setup (class_id=57).

    Attributes:
        1: logical_name (static)
        2: llc_type_1_enable (dynamic)
        3: llc_type_1_parameters (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_8802_2_LLC_TYPE_1_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    llc_type_1_enable: Optional[bool] = False
    llc_type_1_parameters: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'llc_type_1_enable', 3: 'llc_type_1_parameters'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

