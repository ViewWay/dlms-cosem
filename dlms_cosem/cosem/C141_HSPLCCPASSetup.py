"""IC class 141 - HSPLCCPASSetup.

HS-PLC ISO/IEC 12139-1 CPAS Setup - HS-PLC CPAS configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=141
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class HSPLCCPASSetup:
    """COSEM IC HSPLCCPASSetup (class_id=141).

    Attributes:
        1: logical_name (static)
        2: cpas_enable (dynamic)
        3: cpas_mtu (dynamic)
        4: cpas_fragmentation_timeout (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.HS_PLC_IEC_12139_1_CPAS_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    cpas_enable: Optional[bool] = False
    cpas_mtu: Optional[int] = 0
    cpas_fragmentation_timeout: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'cpas_enable', 3: 'cpas_mtu', 4: 'cpas_fragmentation_timeout'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

