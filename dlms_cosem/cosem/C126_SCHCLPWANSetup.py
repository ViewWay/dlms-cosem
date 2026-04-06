"""IC class 126 - SCHCLPWANSetup.

SCHC LPWAN Setup - SCHC (Static Context Header Compression) LPWAN configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=126
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SCHCLPWANSetup:
    """COSEM IC SCHCLPWANSetup (class_id=126).

    Attributes:
        1: logical_name (static)
        2: schc_rule_list (dynamic)
        3: schc_parameter_list (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SCHC_LPWAN
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    schc_rule_list: List[Any] = attr.ib(factory=list)
    schc_parameter_list: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'schc_rule_list', 3: 'schc_parameter_list'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

