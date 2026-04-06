"""IC class 116 - IEC62055Attributes.

IEC 62055-41 Attributes - STS (Standard Transfer Specification) key attributes.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=116
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC62055Attributes:
    """COSEM IC IEC62055Attributes (class_id=116).

    Attributes:
        1: logical_name (static)
        2: sts_key_identification_no (dynamic)
        3: sts_key_revision_no (dynamic)
        4: sts_key_expiry_date (dynamic)
        5: sts_token_carrier_identification (dynamic)
        6: sts_token_decoder_key_status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_62055_ATTRIBUTES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    sts_key_identification_no: Optional[int] = 0
    sts_key_revision_no: Optional[int] = 0
    sts_key_expiry_date: Optional[bytes] = None
    sts_token_carrier_identification: Optional[bytes] = None
    sts_token_decoder_key_status: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'sts_key_identification_no', 3: 'sts_key_revision_no', 4: 'sts_key_expiry_date', 5: 'sts_token_carrier_identification', 6: 'sts_token_decoder_key_status'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

