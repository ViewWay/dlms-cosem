"""IC class 123 - Array Manager.

Manages array operations on COSEM objects including slicing,
indexing, and bulk operations.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.123
"""
from typing import Any, ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ArrayManager:
    """COSEM IC Array Manager (class_id=123).

    Attributes:
        1: logical_name (static)
        2: data_array (dynamic, array)
        3: array_size (dynamic, unsigned)
        4: element_type (dynamic, enum)
    Methods:
        1: get_element
        2: set_element
        3: append_element
        4: insert_element
        5: remove_element
        6: clear_array
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ARRAY_MANAGER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    data_array: List[Any] = attr.ib(factory=list)
    array_size: int = 0
    element_type: int = 0  # 0: octet-string, 1: integer, 2: unsigned, etc.

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="data_array"),
        3: AttributeDescription(attribute_id=3, attribute_name="array_size"),
        4: AttributeDescription(attribute_id=4, attribute_name="element_type"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "get_element",
        2: "set_element",
        3: "append_element",
        4: "insert_element",
        5: "remove_element",
        6: "clear_array",
    }

    def get_element(self, index: int) -> Any:
        """Method 1: Get an element by index."""
        if 0 <= index < len(self.data_array):
            return self.data_array[index]
        return None

    def set_element(self, index: int, value: Any) -> bool:
        """Method 2: Set an element at index."""
        if 0 <= index < len(self.data_array):
            self.data_array[index] = value
            self.array_size = len(self.data_array)
            return True
        return False

    def append_element(self, value: Any) -> bool:
        """Method 3: Append an element to the end."""
        self.data_array.append(value)
        self.array_size = len(self.data_array)
        return True

    def insert_element(self, index: int, value: Any) -> bool:
        """Method 4: Insert an element at index."""
        if 0 <= index <= len(self.data_array):
            self.data_array.insert(index, value)
            self.array_size = len(self.data_array)
            return True
        return False

    def remove_element(self, index: int) -> bool:
        """Method 5: Remove an element at index."""
        if 0 <= index < len(self.data_array):
            self.data_array.pop(index)
            self.array_size = len(self.data_array)
            return True
        return False

    def clear_array(self) -> None:
        """Method 6: Clear all elements."""
        self.data_array = []
        self.array_size = 0

    def get_slice(self, start: int, end: int) -> List[Any]:
        """Get a slice of the array."""
        if start < 0:
            start = 0
        if end > len(self.data_array):
            end = len(self.data_array)
        return self.data_array[start:end]

    def get_element_count(self) -> int:
        """Get the number of elements."""
        return len(self.data_array)

    def set_element_type(self, elem_type: int) -> None:
        """Set the element type."""
        self.element_type = elem_type

    def find_element(self, value: Any) -> int:
        """Find an element and return its index, or -1 if not found."""
        try:
            return self.data_array.index(value)
        except ValueError:
            return -1

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
