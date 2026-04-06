"""IC class 55 - IEC61334LLCSetup.

IEC 61334-4-32 LLC Setup - LLC setup for IEC 61334-4-32.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=55
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC61334LLCSetup:
    """COSEM IC IEC61334LLCSetup (class_id=55).

    Attributes:
        1: logical_name (static)
        2: llc_type_1_enable (dynamic)
        3: llc_type_2_enable (dynamic)
        4: llc_type_3_enable (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_IEC_61334_4_32_LLC_SETUP
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    llc_type_1_enable: Optional[bool] = False
    llc_type_2_enable: Optional[bool] = False
    llc_type_3_enable: Optional[bool] = False

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'llc_type_1_enable', 3: 'llc_type_2_enable', 4: 'llc_type_3_enable'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

