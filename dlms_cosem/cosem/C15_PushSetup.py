"""IC class 40 - Push Setup.

Push notification configuration for automatic data delivery.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.3
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class PushSetup:
    """COSEM IC Push Setup (class_id=40).

    Attributes:
        1: logical_name (static)
        2: push_object_list (dynamic) - List of objects to push
        3: send_destination_and_method (dynamic) - Push delivery method
        4: communication_window (dynamic) - Time windows for push
        5: randomisation_start_interval (dynamic) - Random delay
        6: number_of_retries (dynamic) - Retry count
        7: repetition_delay (dynamic) - Delay between retries
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.PUSH
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    push_object_list: List[Dict[str, Any]] = attr.ib(factory=list)
    send_destination_and_method: Optional[Dict[str, Any]] = None
    communication_window: List[Dict[str, Any]] = attr.ib(factory=list)
    randomisation_start_interval: int = 0
    number_of_retries: int = 3
    repetition_delay: int = 60

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="push_object_list"),
        3: AttributeDescription(attribute_id=3, attribute_name="send_destination_and_method"),
        4: AttributeDescription(attribute_id=4, attribute_name="communication_window"),
        5: AttributeDescription(attribute_id=5, attribute_name="randomisation_start_interval"),
        6: AttributeDescription(attribute_id=6, attribute_name="number_of_retries"),
        7: AttributeDescription(attribute_id=7, attribute_name="repetition_delay"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset push configuration to defaults."""
        self.push_object_list = []
        self.send_destination_and_method = None
        self.communication_window = []
        self.randomisation_start_interval = 0
        self.number_of_retries = 3
        self.repetition_delay = 60

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def add_push_object(self, class_id: int, obis: Obis, attribute_id: int) -> None:
        """Add an object to the push list."""
        self.push_object_list.append({
            "class_id": class_id,
            "logical_name": obis,
            "attribute_id": attribute_id,
        })
