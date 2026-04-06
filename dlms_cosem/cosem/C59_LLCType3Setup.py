"""IC class 59 - LLCType3Setup.

IEC 8802-2 LLC Type 3 Setup - LLC Type 3 acknowledged connectionless setup.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=59
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LLCType3Setup:
    """COSEM IC LLCType3Setup (class_id=59).

    Attributes:
        1: logical_name (static)
        2: llc_type_3_enable (dynamic)
        3: llc_type_3_parameters (dynamic)
        4: llc_type_3_window_size (dynamic)
        5: llc_type_3_retry_count (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_8802_2_LLC_TYPE_3_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    llc_type_3_enable: Optional[bool] = False
    llc_type_3_parameters: List[Any] = attr.ib(factory=list)
    llc_type_3_window_size: Optional[int] = 0
    llc_type_3_retry_count: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'llc_type_3_enable', 3: 'llc_type_3_parameters', 4: 'llc_type_3_window_size', 5: 'llc_type_3_retry_count'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

