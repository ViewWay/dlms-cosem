"""IC class 115 - TokenGateway.

Token Gateway - manages token-based operations for payment meters.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=115
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class TokenGateway:
    """COSEM IC TokenGateway (class_id=115).

    Attributes:
        1: logical_name (static)
        2: token (dynamic)
        3: token_time (dynamic)
        4: token_status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.TOKEN_GATEWAY
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    token: Optional[bytes] = None
    token_time: Optional[bytes] = None
    token_status: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'token', 3: 'token_time', 4: 'token_status'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

