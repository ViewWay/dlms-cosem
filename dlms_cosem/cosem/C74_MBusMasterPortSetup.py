"""IC class 74 - MBusMasterPortSetup.

M-Bus Master Port Setup - configuration for M-Bus master port.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=74
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class MBusMasterPortSetup:
    """COSEM IC MBusMasterPortSetup (class_id=74).

    Attributes:
        1: logical_name (static)
        2: comm_speed (dynamic)
        3: rec_timeout (dynamic)
        4: send_timeout (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_MASTER_PORT_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    comm_speed: Optional[int] = 0
    rec_timeout: Optional[int] = 0
    send_timeout: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'comm_speed', 3: 'rec_timeout', 4: 'send_timeout'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

