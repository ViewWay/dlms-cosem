"""IC class 6 - Register Activation.

Activates/deactivates a register based on conditions (e.g., tariff).

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class RegisterActivation:
    """COSEM IC Register Activation (class_id=6).

    Attributes:
        1: logical_name (static)
        2: register_assignment (static) - list of CosemAttribute
        3: activation_mask (static) - bitmask
        4: active_mask (dynamic)
    Methods:
        1: activate
        2: deactivate
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.REGISTER_ACTIVATION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    register_assignment: List[str] = attr.ib(factory=list)
    activation_mask: int = 0
    active_mask: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="register_assignment"),
        3: AttributeDescription(attribute_id=3, attribute_name="activation_mask"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        4: AttributeDescription(attribute_id=4, attribute_name="active_mask"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "activate", 2: "deactivate"}

    def activate(self, mask: int) -> None:
        self.active_mask |= mask

    def deactivate(self, mask: int) -> None:
        self.active_mask &= ~mask

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
