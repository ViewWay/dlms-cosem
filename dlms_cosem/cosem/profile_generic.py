from enum import IntEnum
from typing import *

import attr

from dlms_cosem import cosem
from dlms_cosem import enumerations as enums
from dlms_cosem import parsers
from dlms_cosem.cosem.selective_access import CaptureObject, RangeDescriptor


class SortMethod(IntEnum):
    FIFO = 1
    LIFO = 2
    LARGEST = 3
    SMALLEST = 4
    NEAREST_TO_ZERO = 5
    FARTHEST_FROM_ZERO = 6


class ProfileType(IntEnum):
    LOAD_PROFILE = 0
    BILLING = 1
    DAILY = 2
    MONTHLY = 3
    EVENT = 4


class BufferOverflow(IntEnum):
    """Buffer overflow handling strategy."""
    OLDEST_DISCARDED = 0
    NEWEST_DISCARDED = 1
    OVERWRITE_OLDEST = 2


@attr.s(auto_attribs=True)
class AttributeDescription:
    attribute_id: int
    attribute_name: str
    data_parser: Optional[Any] = attr.ib(default=None)
    data_converter: Optional[Any] = attr.ib(default=None)  # callable?


@attr.s(auto_attribs=True)
class Data:
    INTERFACE_CLASS_ID: ClassVar[enums.CosemInterface] = enums.CosemInterface.DATA

    logical_name: cosem.Obis
    value: Any

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }

    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="value"),
    }

    SELECTIVE_ACCESS: ClassVar[Dict[int, Type[RangeDescriptor]]] = {}

    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "capture"}

    DYNAMIC_CONVERTERS: ClassVar[Dict[int, Callable]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES.keys()


def convert_load_profile(instance, data):
    parser = parsers.ProfileGenericBufferParser(
        capture_objects=[x.cosem_attribute for x in instance.capture_objects],
        capture_period=instance.capture_period,
    )
    return parser.parse_entries(data)


@attr.s(auto_attribs=True)
class ProfileGeneric:
    """Enhanced COSEM IC Profile Generic (class_id=7).

    Supports multiple profile types, buffer overflow handling,
    entry range reading via EntryDescriptor, and sorting.

    Attributes:
        1: logical_name (static)
        2: buffer (dynamic) - list of captured entries
        3: capture_objects (static)
        4: capture_period (static, seconds)
        5: sort_method (static)
        6: sort_object (static)
        7: entries_in_use (dynamic)
        8: profile_entries (static) - max buffer size
    Methods:
        1: reset
        2: capture
    """

    INTERFACE_CLASS_ID: ClassVar[enums.CosemInterface] = (
        enums.CosemInterface.PROFILE_GENERIC
    )

    logical_name: cosem.Obis
    buffer: List[List[Any]] = attr.ib(factory=list)
    capture_objects: List[CaptureObject] = attr.ib(factory=list)
    capture_period: int = 0
    sort_method: Optional[SortMethod] = attr.ib(default=None)
    sort_object: Optional[CaptureObject] = attr.ib(default=None)
    entries_in_use: int = 0
    profile_entries: Optional[int] = attr.ib(default=None)
    profile_type: ProfileType = attr.ib(default=ProfileType.LOAD_PROFILE)
    overflow_strategy: BufferOverflow = attr.ib(default=BufferOverflow.OLDEST_DISCARDED)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_objects"),
        4: AttributeDescription(attribute_id=4, attribute_name="capture_period"),
        5: AttributeDescription(attribute_id=5, attribute_name="sort_method"),
        6: AttributeDescription(attribute_id=6, attribute_name="sort_object"),
        8: AttributeDescription(attribute_id=8, attribute_name="profile_entries"),
    }

    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="buffer"),
        7: AttributeDescription(attribute_id=7, attribute_name="entries_in_use"),
    }

    SELECTIVE_ACCESS: ClassVar[Dict[int, Type[RangeDescriptor]]] = {2: RangeDescriptor}

    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "capture"}

    DYNAMIC_CONVERTERS: ClassVar[Dict[int, Callable]] = {2: convert_load_profile}

    def reset(self, data: int = 0):
        """Clears the buffer."""
        self.buffer = []
        self.entries_in_use = 0

    def capture(self, values: List[Any]) -> None:
        """Add a new capture entry to the buffer."""
        self.buffer.append(values)
        self.entries_in_use = len(self.buffer)

        # Handle overflow
        if self.profile_entries and len(self.buffer) > self.profile_entries:
            if self.overflow_strategy == BufferOverflow.OLDEST_DISCARDED:
                self.buffer = self.buffer[-self.profile_entries:]
            elif self.overflow_strategy == BufferOverflow.NEWEST_DISCARDED:
                self.buffer = self.buffer[:self.profile_entries]
            elif self.overflow_strategy == BufferOverflow.OVERWRITE_OLDEST:
                self.buffer = self.buffer[-self.profile_entries:]
            self.entries_in_use = len(self.buffer)

    def read_range(self, start_index: int, end_index: int = 0) -> List[List[Any]]:
        """Read entries in a range. end_index=0 means from start to end."""
        if end_index == 0:
            return self.buffer[start_index:]
        return self.buffer[start_index:end_index]

    def read_by_entry_descriptor(self, from_index: int,
                                  to_index: int,
                                  access_selector: int = 0) -> List[List[Any]]:
        """Read entries using EntryDescriptor (selective access).

        Args:
            from_index: Starting entry index (1-based, 0 = oldest)
            to_index: Ending entry index (0 = newest)
            access_selector: 0=range, 1=last n entries
        """
        if access_selector == 1:
            # Last n entries
            n = from_index
            return self.buffer[-n:] if n > 0 else []
        else:
            # Range access
            start = from_index if from_index > 0 else 0
            end = to_index if to_index > 0 else len(self.buffer)
            return self.buffer[start:end]

    def sort_buffer(self) -> None:
        """Sort buffer entries according to sort_method."""
        if not self.sort_method or not self.buffer:
            return

        if self.sort_method == SortMethod.FIFO:
            pass  # already in FIFO order
        elif self.sort_method == SortMethod.LIFO:
            self.buffer.reverse()
        elif self.sort_method == SortMethod.LARGEST:
            # Sort by first column value descending
            self.buffer.sort(key=lambda x: x[0] if x else 0, reverse=True)
        elif self.sort_method == SortMethod.SMALLEST:
            self.buffer.sort(key=lambda x: x[0] if x else 0)
        elif self.sort_method == SortMethod.NEAREST_TO_ZERO:
            self.buffer.sort(key=lambda x: abs(x[0]) if x else 0)
        elif self.sort_method == SortMethod.FARTHEST_FROM_ZERO:
            self.buffer.sort(key=lambda x: abs(x[0]) if x else 0, reverse=True)

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES.keys()
