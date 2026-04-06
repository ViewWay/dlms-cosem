"""IC class 143 - HSPLCHDLCSSASSetup.

HS-PLC ISO/IEC 12139-1 HDLC SSAS Setup - HS-PLC HDLC SSAS configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=143
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class HSPLCHDLCSSASSetup:
    """COSEM IC HSPLCHDLCSSASSetup (class_id=143).

    Attributes:
        1: logical_name (static)
        2: hdlc_ssas_enable (dynamic)
        3: hdlc_ssas_mtu (dynamic)
        4: hdlc_ssas_fragmentation_timeout (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.HS_PLC_IEC_12139_1_HDLC_SSAS_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    hdlc_ssas_enable: Optional[bool] = False
    hdlc_ssas_mtu: Optional[int] = 0
    hdlc_ssas_fragmentation_timeout: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'hdlc_ssas_enable', 3: 'hdlc_ssas_mtu', 4: 'hdlc_ssas_fragmentation_timeout'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

