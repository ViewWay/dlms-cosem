"""IC class 86 - PRIMEAppIdentification.

PRIME NB OFDM PLC Application Identification - PRIME app identification.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=86
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class PRIMEAppIdentification:
    """COSEM IC PRIMEAppIdentification (class_id=86).

    Attributes:
        1: logical_name (static)
        2: application_name (dynamic)
        3: application_version (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PRIME_OFDM_PLC_MAC_APPLICATION_IDENTIFICATION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    application_name: Optional[str] = ''
    application_version: Optional[str] = ''

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'application_name', 3: 'application_version'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

