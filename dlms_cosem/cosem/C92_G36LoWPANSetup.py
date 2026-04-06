"""IC class 92 - G36LoWPANSetup.

G3-PLC 6LoWPAN Adaptation Layer Setup - G3-PLC 6LoWPAN configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=92
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class G36LoWPANSetup:
    """COSEM IC G36LoWPANSetup (class_id=92).

    Attributes:
        1: logical_name (static)
        2: lowpan_enable (dynamic)
        3: lowpan_mtu (dynamic)
        4: lowpan_fragmentation_timeout (dynamic)
        5: lowpan_fragmentation_retries (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.G3_PLC_6LOWPAN_ADAPTATION_LAYER_SETUP
    VERSION: ClassVar[int] = 4

    logical_name: Obis
    lowpan_enable: Optional[bool] = False
    lowpan_mtu: Optional[int] = 0
    lowpan_fragmentation_timeout: Optional[int] = 0
    lowpan_fragmentation_retries: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'lowpan_enable', 3: 'lowpan_mtu', 4: 'lowpan_fragmentation_timeout', 5: 'lowpan_fragmentation_retries'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

