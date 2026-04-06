"""IC class 83 - PRIMEMACFuncParams.

PRIME NB OFDM PLC MAC Functional Parameters - PRIME MAC functional params.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=83
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMEMACFuncParams:
    """COSEM IC PRIMEMACFuncParams (class_id=83).

    Attributes:
        1: logical_name (static)
        2: mac_address (dynamic)
        3: mac_frame_counter (dynamic)
        4: mac_key (dynamic)
        5: mac_switch (dynamic)
        6: mac_security_enabled (dynamic)
        7: mac_security_level (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_OFDM_PLC_MAC_FUNCTIONAL_PARAMETERS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mac_address: Optional[bytes] = None
    mac_frame_counter: Optional[int] = 0
    mac_key: Optional[bytes] = None
    mac_switch: Optional[bool] = False
    mac_security_enabled: Optional[bool] = False
    mac_security_level: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mac_address', 3: 'mac_frame_counter', 4: 'mac_key', 5: 'mac_switch', 6: 'mac_security_enabled', 7: 'mac_security_level'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

