from typing import *
from enum import IntEnum

import attr

from dlms_cosem import cosem, dlms_data
from dlms_cosem import enumerations as enums
from dlms_cosem.protocol.xdlms.base import AbstractXDlmsApdu
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority

"""
Selective-Access-Descriptor ::= CHOICE
{
    range-descriptor            [0] IMPLICIT RangeDescriptor,
    entry-descriptor            [1] IMPLICIT EntryDescriptor,
    selected-values             [2] IMPLICIT SelectedValues
}

RangeDescriptor ::= SEQUENCE
{
    restricting-identifier      OctetString,  -- 1 byte: entry, 2: from_entry, 3: to_entry, 4: from/to
    selected-object-attribute   Unsigned8 OPTIONAL
}

EntryDescriptor ::= Structure containing COSEM object identification

SelectedValues ::= Structure containing list of selected values
"""


class AccessSelectionType(IntEnum):
    RANGE_DESCRIPTOR = 0
    ENTRY_DESCRIPTOR = 1
    SELECTED_VALUES = 2


@attr.s(auto_attribs=True)
class RangeDescriptor:
    """
    Range Descriptor for selective access.

    restricting-identifier is a 1-byte code:
      0: not used
      1: entry (single entry)
      2: from-entry (range start)
      3: to-entry (range end)
      4: from-entry / to-entry (range with both)
    """
    restricting_identifier: int
    selected_object_attribute: Optional[int] = attr.ib(default=None)
    range_start: Optional[int] = attr.ib(default=None)
    range_end: Optional[int] = attr.ib(default=None)

    @classmethod
    def from_bytes(cls, data: bytearray) -> "RangeDescriptor":
        restricting_id = data.pop(0)
        obj_attr = None
        range_start = None
        range_end = None

        # remaining data depends on restricting_id:
        # 1: 1 value (entry index)
        # 2: 1 value (from_entry)
        # 3: 1 value (to_entry)
        # 4: 2 values (from_entry, to_entry)
        # All values are encoded as variable integers
        if restricting_id == 1:
            range_start, _ = dlms_data.decode_variable_integer(bytes(data))
        elif restricting_id == 2:
            range_start, remaining = dlms_data.decode_variable_integer(bytes(data))
        elif restricting_id == 3:
            range_end, _ = dlms_data.decode_variable_integer(bytes(data))
        elif restricting_id == 4:
            range_start, remaining = dlms_data.decode_variable_integer(bytes(data))
            range_end, _ = dlms_data.decode_variable_integer(remaining)

        return cls(
            restricting_identifier=restricting_id,
            selected_object_attribute=obj_attr,
            range_start=range_start,
            range_end=range_end,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.restricting_identifier)
        if self.selected_object_attribute is not None:
            out.append(self.selected_object_attribute)
        if self.range_start is not None:
            out.extend(dlms_data.encode_variable_integer(self.range_start))
        if self.range_end is not None:
            out.extend(dlms_data.encode_variable_integer(self.range_end))
        return bytes(out)


@attr.s(auto_attribs=True)
class EntryDescriptor:
    """
    Entry Descriptor for selective access.
    Encoded as a DLMS Structure.
    """
    entries: list = attr.ib(factory=list)

    @classmethod
    def from_bytes(cls, data: bytearray) -> "EntryDescriptor":
        # Parse as DLMS structure: first byte is structure tag, then length
        # The data should already start after the choice tag
        entries = []
        # Read the number of elements
        count, remaining = dlms_data.decode_variable_integer(bytes(data))
        data = bytearray(remaining)
        for _ in range(count):
            val_len, remaining = dlms_data.decode_variable_integer(bytes(data))
            data = bytearray(remaining)
            entry = bytes(data[:val_len])
            data = data[val_len:]
            entries.append(entry)
        return cls(entries=entries)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.extend(dlms_data.encode_variable_integer(len(self.entries)))
        for entry in self.entries:
            out.extend(dlms_data.encode_variable_integer(len(entry)))
            out.extend(entry)
        return bytes(out)


@attr.s(auto_attribs=True)
class SelectedValues:
    """
    Selected Values for selective access.
    Encoded as a DLMS Array of indices.
    """
    values: list = attr.ib(factory=list)

    @classmethod
    def from_bytes(cls, data: bytearray) -> "SelectedValues":
        values = []
        count, remaining = dlms_data.decode_variable_integer(bytes(data))
        data = bytearray(remaining)
        for _ in range(count):
            val_len, remaining = dlms_data.decode_variable_integer(bytes(data))
            data = bytearray(remaining)
            value = bytes(data[:val_len])
            data = data[val_len:]
            values.append(value)
        return cls(values=values)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.extend(dlms_data.encode_variable_integer(len(self.values)))
        for value in self.values:
            out.extend(dlms_data.encode_variable_integer(len(value)))
            out.extend(value)
        return bytes(out)


def parse_access_selection(data: bytearray):
    """
    Parse a Selective-Access-Descriptor from bytes.

    The first byte is the choice tag (0, 1, or 2).
    Returns the appropriate descriptor object.
    """
    choice_tag = data.pop(0)
    if choice_tag == AccessSelectionType.RANGE_DESCRIPTOR:
        return RangeDescriptor.from_bytes(data)
    elif choice_tag == AccessSelectionType.ENTRY_DESCRIPTOR:
        return EntryDescriptor.from_bytes(data)
    elif choice_tag == AccessSelectionType.SELECTED_VALUES:
        return SelectedValues.from_bytes(data)
    else:
        raise ValueError(f"Unknown access selection type: {choice_tag}")


def access_selection_to_bytes(access_selection) -> bytes:
    """
    Serialize an access selection descriptor to bytes.
    """
    out = bytearray()
    if isinstance(access_selection, RangeDescriptor):
        out.append(AccessSelectionType.RANGE_DESCRIPTOR)
        out.extend(access_selection.to_bytes())
    elif isinstance(access_selection, EntryDescriptor):
        out.append(AccessSelectionType.ENTRY_DESCRIPTOR)
        out.extend(access_selection.to_bytes())
    elif isinstance(access_selection, SelectedValues):
        out.append(AccessSelectionType.SELECTED_VALUES)
        out.extend(access_selection.to_bytes())
    else:
        raise ValueError(f"Unknown access selection type: {type(access_selection)}")
    return bytes(out)

"""
Set-Request ::= CHOICE
{
set-request-normal                          [1] IMPLICIT Set-Request-Normal,
set-request-with-first-datablock            [2] IMPLICIT Set-Request-With-First-Datablock,
set-request-with-datablock                  [3] IMPLICIT Set-Request-With-Datablock,
set-request-with-list                       [4] IMPLICIT Set-Request-With-List,
set-request-with-list-and-first-datablock   [5] IMPLICIT Set-Request-With-List-And-First-Datablock
}

Set-Response ::= CHOICE
{
set-response-normal                     [1] IMPLICIT Set-Response-Normal,
set-response-datablock                  [2] IMPLICIT Set-Response-Datablock,
set-response-last-datablock             [3] IMPLICIT Set-Response-Last-Datablock,
set-response-last-datablock-with-list   [4] IMPLICIT Set-Response-Last-Datablock-With-List,
set-response-with-list                  [5] IMPLICIT Set-Response-With-List
}
"""


@attr.s(auto_attribs=True)
class SetRequestNormal(AbstractXDlmsApdu):
    """
    Set-Request-Normal ::= SEQUENCE
    {
        invoke-id-and-priority          Invoke-Id-And-Priority,
        cosem-attribute-descriptor      Cosem-Attribute-Descriptor,
        access-selection                Selective-Access-Descriptor OPTIONAL,
        value                           Data
    }
    """

    TAG: ClassVar[int] = 193
    RESPONSE_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.NORMAL
    cosem_attribute: cosem.CosemAttribute = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemAttribute)
    )
    data: bytes = attr.ib(validator=attr.validators.instance_of(bytes))
    access_selection: Optional[Any] = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.NORMAL:
            raise ValueError("The type of the SetRequest is not for a SetRequestNormal")

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )
        cosem_attribute = cosem.CosemAttribute.from_bytes(data[:9])
        data = data[9:]

        has_access_selection = bool(data.pop(0))
        if has_access_selection:
            access_selection = parse_access_selection(data)
        else:
            access_selection = None

        return cls(
            cosem_attribute=cosem_attribute,
            data=bytes(data),
            access_selection=access_selection,
            invoke_id_and_priority=invoke_id_and_priority,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_attribute.to_bytes())
        if self.access_selection:
            out.extend(b"\x01")
            out.extend(access_selection_to_bytes(self.access_selection))
        else:
            out.extend(b"\x00")
        out.extend(self.data)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithFirstBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-First-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority      Invoke-Id-And-Priority,
    cosem-attribute-descriptor  Cosem-Attribute-Descriptor,
    access-selection            [0] IMPLICIT Selective-Access-Descriptor OPTIONAL,
    datablock                   DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 193
    REQUEST_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.WITH_FIRST_BLOCK

    cosem_attribute: cosem.CosemAttribute = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemAttribute)
    )
    access_selection: Optional[Any] = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.WITH_FIRST_BLOCK:
            raise ValueError(
                "The type of the SetRequest is not for a SetRequestWithFirstBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Cosem attribute descriptor
        cosem_attribute = cosem.CosemAttribute.from_bytes(bytes(data[:9]))
        data = data[9:]

        # Access selection (optional)
        has_access_selection = bool(data.pop(0))
        access_selection = None
        if has_access_selection:
            access_selection = parse_access_selection(data)

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number_bytes = bytes(data[:4])
        block_number = int.from_bytes(block_number_bytes, "big")
        data = data[4:]

        # raw-data (OCTET STRING)
        data_length, remaining = dlms_data.decode_variable_integer(bytes(data))
        data_block = bytes(remaining[:data_length])

        return cls(
            cosem_attribute=cosem_attribute,
            access_selection=access_selection,
            invoke_id_and_priority=invoke_id_and_priority,
            last_block=last_block,
            block_number=block_number,
            data_block=data_block,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.REQUEST_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_attribute.to_bytes())

        # Access selection
        if self.access_selection:
            out.extend(b"\x01")
            out.extend(access_selection_to_bytes(self.access_selection))
        else:
            out.extend(b"\x00")

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))

        # raw-data
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    datablock               DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 193
    REQUEST_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.WITH_BLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.WITH_BLOCK:
            raise ValueError(
                "The type of the SetRequest is not for a SetRequestWithBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number_bytes = bytes(data[:4])
        block_number = int.from_bytes(block_number_bytes, "big")
        data = data[4:]

        # raw-data (OCTET STRING)
        data_length, remaining = dlms_data.decode_variable_integer(bytes(data))
        data_block = bytes(remaining[:data_length])

        return cls(
            invoke_id_and_priority=invoke_id_and_priority,
            last_block=last_block,
            block_number=block_number,
            data_block=data_block,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.REQUEST_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))

        # raw-data
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithList(AbstractXDlmsApdu):
    """
    Set-Request-With-List ::= SEQUENCE
    {
    invoke-id-and-priority      Invoke-Id-And-Priority,
    attribute-descriptor-list   SEQUENCE OF Cosem-Attribute-Descriptor-With-Selection,
    value-list                  SEQUENCE OF Data
    }

    Cosem-Attribute-Descriptor-With-Selection ::= SEQUENCE
    {
    cosem-attribute-descriptor   Cosem-Attribute-Descriptor,
    access-selection             Selective-Access-Descriptor OPTIONAL
    }
    """

    TAG: ClassVar[int] = 193
    REQUEST_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.WITH_LIST

    attribute_descriptor_list: List[cosem.CosemAttribute] = attr.ib(
        factory=list
    )
    value_list: List[bytes] = attr.ib(factory=list)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.WITH_LIST:
            raise ValueError(
                "The type of the SetRequest is not for a SetRequestWithList"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of attribute descriptors
        num_attributes = data.pop(0)

        attribute_descriptor_list = []
        for _ in range(num_attributes):
            # Parse CosemAttribute (9 bytes)
            cosem_attribute = cosem.CosemAttribute.from_bytes(bytes(data[:9]))
            data = data[9:]
            # Skip access selection for now
            has_access = bool(data.pop(0))
            if has_access:
                parse_access_selection(data)
            attribute_descriptor_list.append(cosem_attribute)

        # Number of values
        num_values = data.pop(0)

        value_list = []
        for _ in range(num_values):
            # Parse value (assuming simple octet string for now)
            value_length, remaining_bytes = dlms_data.decode_variable_integer(bytes(data))
            data = bytearray(remaining_bytes)
            value = bytes(data[:value_length])
            data = data[value_length:]
            value_list.append(value)

        return cls(
            attribute_descriptor_list=attribute_descriptor_list,
            value_list=value_list,
            invoke_id_and_priority=invoke_id_and_priority,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.REQUEST_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # Number of attribute descriptors
        out.append(len(self.attribute_descriptor_list))

        # Attribute descriptors
        for attr_desc in self.attribute_descriptor_list:
            out.extend(attr_desc.to_bytes())
            out.append(0x00)  # No access selection

        # Number of values
        out.append(len(self.value_list))

        # Values
        for value in self.value_list:
            out.extend(dlms_data.encode_variable_integer(len(value)))
            out.extend(value)

        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestWithListFirstBlock(AbstractXDlmsApdu):
    """
    Set-Request-With-List-And-First-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    attribute-descriptor-list  SEQUENCE OF Cosem-Attribute-Descriptor-With-Selection,
    datablock DataBlock-SA
    }

    Cosem-Attribute-Descriptor-With-Selection ::= SEQUENCE
    {
    cosem-attribute-descriptor   Cosem-Attribute-Descriptor,
    access-selection             Selective-Access-Descriptor OPTIONAL
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 193
    REQUEST_TYPE: ClassVar[enums.SetRequestType] = enums.SetRequestType.FIRST_BLOCK_WITH_LIST

    attribute_descriptor_list: List[cosem.CosemAttribute] = attr.ib(
        factory=list
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetRequest is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetRequestType(data.pop(0))
        if type_choice is not enums.SetRequestType.FIRST_BLOCK_WITH_LIST:
            raise ValueError(
                "The type of the SetRequest is not for a SetRequestWithListFirstBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of attribute descriptors
        num_attributes = data.pop(0)

        attribute_descriptor_list = []
        for _ in range(num_attributes):
            # Parse CosemAttribute (9 bytes)
            cosem_attribute = cosem.CosemAttribute.from_bytes(bytes(data[:9]))
            data = data[9:]
            # Skip access selection
            has_access = bool(data.pop(0))
            if has_access:
                _ = data.pop(0)
            attribute_descriptor_list.append(cosem_attribute)

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number_bytes = bytes(data[:4])
        block_number = int.from_bytes(block_number_bytes, "big")
        data = data[4:]

        # raw-data (OCTET STRING)
        data_length, remaining = dlms_data.decode_variable_integer(bytes(data))
        data_block = bytes(remaining[:data_length])

        return cls(
            attribute_descriptor_list=attribute_descriptor_list,
            invoke_id_and_priority=invoke_id_and_priority,
            last_block=last_block,
            block_number=block_number,
            data_block=data_block,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.REQUEST_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # Number of attribute descriptors
        out.append(len(self.attribute_descriptor_list))

        # Attribute descriptors
        for attr_desc in self.attribute_descriptor_list:
            out.extend(attr_desc.to_bytes())
            out.append(0x00)  # No access selection

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))

        # raw-data
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)


@attr.s(auto_attribs=True)
class SetRequestFactory:
    """
    The factory will parse the SetRequest and return either a SetRequest type class
    """

    TAG: ClassVar[int] = 193

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != SetRequestFactory.TAG:
            raise ValueError(
                f"Tag for SET request is not correct. Got {tag}, should be "
                f"{SetRequestFactory.TAG}"
            )
        request_type = enums.SetRequestType(data.pop(0))
        if request_type == enums.SetRequestType.NORMAL:
            return SetRequestNormal.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.WITH_FIRST_BLOCK:
            return SetRequestWithFirstBlock.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.WITH_BLOCK:
            return SetRequestWithBlock.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.WITH_LIST:
            return SetRequestWithList.from_bytes(source_bytes)
        elif request_type == enums.SetRequestType.FIRST_BLOCK_WITH_LIST:
            return SetRequestWithListFirstBlock.from_bytes(source_bytes)
        else:
            raise ValueError(f"Unknown SetRequestType: {request_type}")


@attr.s(auto_attribs=True)
class SetResponseNormal(AbstractXDlmsApdu):
    """
    Set-Response-Normal ::= SEQUENCE
    {
        invoke-id-and-priority Invoke-Id-And-Priority,
        result  Data-Access-Result
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.NORMAL
    result: enums.DataAccessResult = attr.ib(
        validator=attr.validators.instance_of(enums.DataAccessResult)
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.NORMAL:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseNormal"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        result = enums.DataAccessResult(data.pop(0))

        return cls(result=result, invoke_id_and_priority=invoke_id_and_priority)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.result.value)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseWithBlock(AbstractXDlmsApdu):
    """
    Set-Response-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.WITH_BLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(default=0)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.WITH_BLOCK:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseWithBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        block_number = int.from_bytes(bytes(data[:4]), "big")

        return cls(invoke_id_and_priority=invoke_id_and_priority, block_number=block_number)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.block_number.to_bytes(4, "big"))
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseLastBlock(AbstractXDlmsApdu):
    """
    Set-Response-Last-Datablock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  Data-Access-Result,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.WITH_LAST_BLOCK

    result: enums.DataAccessResult = attr.ib(
        validator=attr.validators.instance_of(enums.DataAccessResult)
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(default=0)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.WITH_LAST_BLOCK:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseLastBlock"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        result = enums.DataAccessResult(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")

        return cls(
            result=result,
            invoke_id_and_priority=invoke_id_and_priority,
            block_number=block_number,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.result.value)
        out.extend(self.block_number.to_bytes(4, "big"))
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseLastBlockWithList(AbstractXDlmsApdu):
    """
    Set-Response-Last-Datablock-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  SEQUENCE OF Data-Access-Result,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.LAST_BLOCK_WITH_LIST

    result_list: List[enums.DataAccessResult] = attr.ib(factory=list)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(default=0)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.LAST_BLOCK_WITH_LIST:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseLastBlockWithList"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of results
        num_results = data.pop(0)

        result_list = []
        for _ in range(num_results):
            result_list.append(enums.DataAccessResult(data.pop(0)))

        block_number = int.from_bytes(bytes(data[:4]), "big")

        return cls(
            result_list=result_list,
            invoke_id_and_priority=invoke_id_and_priority,
            block_number=block_number,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(len(self.result_list))
        for result in self.result_list:
            out.append(result.value)
        out.extend(self.block_number.to_bytes(4, "big"))
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseWithList(AbstractXDlmsApdu):
    """
    Set-Response-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    result                  SEQUENCE OF Data-Access-Result,
    }
    """

    TAG: ClassVar[int] = 197
    RESPONSE_TYPE: ClassVar[enums.SetResponseType] = enums.SetResponseType.WITH_LIST

    result_list: List[enums.DataAccessResult] = attr.ib(factory=list)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        factory=InvokeIdAndPriority,
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for SetResponse is not correct. Got {tag}, should be {cls.TAG}"
            )

        type_choice = enums.SetResponseType(data.pop(0))
        if type_choice is not enums.SetResponseType.WITH_LIST:
            raise ValueError(
                "The type of the SetResponse is not for a SetResponseWithList"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of results
        num_results = data.pop(0)

        result_list = []
        for _ in range(num_results):
            result_list.append(enums.DataAccessResult(data.pop(0)))

        return cls(
            result_list=result_list, invoke_id_and_priority=invoke_id_and_priority
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.TAG)
        out.append(self.RESPONSE_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(len(self.result_list))
        for result in self.result_list:
            out.append(result.value)
        return bytes(out)


@attr.s(auto_attribs=True)
class SetResponseFactory:
    """
    The factory will parse the SetResponse and return a SetResponse type class
    """

    TAG: ClassVar[int] = 197

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != SetResponseFactory.TAG:
            raise ValueError(
                f"Tag for Set response is not correct. Got {tag}, should be "
                f"{SetResponseFactory.TAG}"
            )
        request_type = enums.SetResponseType(data.pop(0))
        if request_type == enums.SetResponseType.NORMAL:
            return SetResponseNormal.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.WITH_BLOCK:
            return SetResponseWithBlock.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.WITH_LAST_BLOCK:
            return SetResponseLastBlock.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.LAST_BLOCK_WITH_LIST:
            return SetResponseLastBlockWithList.from_bytes(source_bytes)
        elif request_type == enums.SetResponseType.WITH_LIST:
            return SetResponseWithList.from_bytes(source_bytes)
        else:
            raise ValueError(f"Unknown SetResponseType: {request_type}")
