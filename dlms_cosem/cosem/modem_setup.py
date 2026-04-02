"""IC class 27 - Modem Configuration.

Configuration for PSTN modem communication.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ModemSetup:
    """COSEM IC Modem Setup (class_id=27).

    Attributes:
        1: logical_name (static)
        2: communication_speed (static)
        3: modem_initialisation_string (static)
        4: connection_setup_string (static)
        5: post_connection_string (static)
        6: pre_disconnection_string (static)
        7: phone_number (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MODEM_CONFIGURATION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    communication_speed: int = 9600
    modem_init_string: Optional[str] = None
    connection_setup_string: Optional[str] = None
    post_connection_string: Optional[str] = None
    pre_disconnection_string: Optional[str] = None
    phone_number: Optional[str] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="communication_speed"),
        3: AttributeDescription(attribute_id=3, attribute_name="modem_init_string"),
        4: AttributeDescription(attribute_id=4, attribute_name="connection_setup_string"),
        5: AttributeDescription(attribute_id=5, attribute_name="post_connection_string"),
        6: AttributeDescription(attribute_id=6, attribute_name="pre_disconnection_string"),
        7: AttributeDescription(attribute_id=7, attribute_name="phone_number"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
