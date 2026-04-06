"""IC class 80 - PRIMELLCSSCSSetup.

PRIME 61334-4-32 LLC SSCS Setup - PRIME LLC SSCS configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=80
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMELLCSSCSSetup:
    """COSEM IC PRIMELLCSSCSSetup (class_id=80).

    Attributes:
        1: logical_name (static)
        2: sscs_type (dynamic)
        3: sscs_enable (dynamic)
        4: sscs_response_time (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_61344_4_32_LLC_SSCS_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    sscs_type: Optional[int] = 0
    sscs_enable: Optional[bool] = False
    sscs_response_time: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'sscs_type', 3: 'sscs_enable', 4: 'sscs_response_time'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

