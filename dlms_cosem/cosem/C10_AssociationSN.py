"""IC class 12 - Association SN (Short Name).

Association object for SN (Short Name) referencing. Enhanced with HLS-ISM support.

Blue Book: DLMS UA 1000-1 Ed. 14
Yellow Book: DLMS UA 1000-5
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class AssociationSN:
    """COSEM IC Association SN (class_id=12).

    Attributes:
        1: logical_name (static)
        2: object_list (static) - list of CosemObjectListItem
        3: association_status (dynamic)
        4: security_setup_reference (static)
        5: hls_auth_mechanism (static) - AuthenticationMechanism enum
        6: server_system_title (static, 8 bytes)
    Methods:
        1: reply_to_HLS_authentication
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ASSOCIATION_SN
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    object_list: List[Any] = attr.ib(factory=list)
    association_status: int = 0
    security_setup_reference: Optional[str] = None
    hls_auth_mechanism: enums.AuthenticationMechanism = enums.AuthenticationMechanism.HLS_GMAC
    server_system_title: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="object_list"),
        4: AttributeDescription(attribute_id=4, attribute_name="security_setup_reference"),
        5: AttributeDescription(attribute_id=5, attribute_name="hls_auth_mechanism"),
        6: AttributeDescription(attribute_id=6, attribute_name="server_system_title"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        3: AttributeDescription(attribute_id=3, attribute_name="association_status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reply_to_HLS_authentication"}

    def reply_to_HLS_authentication(self, data: bytes) -> None:
        """Method 1: Reply to HLS authentication challenge."""
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
