"""IC class 105 - Modem Configuration (advanced).

Extended modem configuration with connection parameters.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ModemConfiguration:
    """COSEM IC Modem Configuration (class_id=105).

    Attributes:
        1: logical_name (static)
        2: connection_settings (static)
        3: status (dynamic)
    Methods:
        1: connect
        2: disconnect
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.AUTO_CONNECT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    connection_settings: Optional[bytes] = None
    status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="connection_settings"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        3: AttributeDescription(attribute_id=3, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "connect", 2: "disconnect"}

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
