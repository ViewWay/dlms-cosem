"""IC class 152 - CoAPSetup.

CoAP Setup - Constrained Application Protocol configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=152
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class CoAPSetup:
    """COSEM IC CoAPSetup (class_id=152).

    Attributes:
        1: logical_name (static)
        2: coap_server_address (dynamic)
        3: coap_server_port (dynamic)
        4: response_timeout (dynamic)
        5: max_retransmit (dynamic)
        6: ack_timeout (dynamic)
        7: ack_random_factor (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.COAP_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    coap_server_address: Optional[str] = ''
    coap_server_port: Optional[int] = 0
    response_timeout: Optional[int] = 0
    max_retransmit: Optional[int] = 0
    ack_timeout: Optional[int] = 0
    ack_random_factor: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'coap_server_address', 3: 'coap_server_port', 4: 'response_timeout', 5: 'max_retransmit', 6: 'ack_timeout', 7: 'ack_random_factor'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

