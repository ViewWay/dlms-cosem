from typing import *

import attr

from dlms_cosem import cosem, dlms_data
from dlms_cosem import enumerations
from dlms_cosem.protocol.xdlms.base import AbstractXDlmsApdu
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority
from dlms_cosem.cosem.selective_access import AccessDescriptorFactory

# Action-Request ::= CHOICE
# {
# action-request-normal              [1] IMPLICIT Action-Request-Normal,
# action-request-next-pblock         [2] IMPLICIT Action-Request-Next-Pblock,
# action-request-with-list           [3] IMPLICIT Action-Request-With-List,
# action-request-with-first-pblock   [4] IMPLICIT Action-Request-With-First-Pblock,
# action-request-with-list-and-first-pblock [5] IMPLICIT Action-Request-With-List-And-First-Pblock
# }
#
# Action-Response ::= CHOICE
# {
# action-response-normal            [1] IMPLICIT Action-Response-Normal,
# action-response-with-pblock       [2] IMPLICIT Action-Response-With-Pblock,
# action-response-next-pblock       [3] IMPLICIT Action-Response-Next-Pblock,
# action-response-with-list         [4] IMPLICIT Action-Response-With-List,
# action-response-last-pblock       [5] IMPLICIT Action-Response-Last-Pblock
# }


@attr.s(auto_attribs=True)
class ActionRequestNormal(AbstractXDlmsApdu):
    TAG: ClassVar[int] = 195
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NORMAL

    cosem_method: cosem.CosemMethod = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemMethod)
    )
    data: Optional[bytes] = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    access_selection: Optional[
        Union[
            "dlms_cosem.cosem.selective_access.RangeDescriptor",
            "dlms_cosem.cosem.selective_access.EntryDescriptor",
        ]
    ] = attr.ib(default=None)

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_method.to_bytes())
        if self.access_selection:
            # Access selection is encoded after the method
            out.append(0x01)  # Has access selection
            # Encode the access selection descriptor
            access_bytes = self.access_selection.to_bytes()
            out.extend(access_bytes)
        else:
            # No access selection
            out.append(0x00)
        if self.data:
            out.append(0x01)
            out.extend(self.data)
        else:
            out.append(0x00)
        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not the correct tag for an ActionRequest, should "
                f"be {cls.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))

        if request_type != enumerations.ActionType.NORMAL:
            raise ValueError(
                f"Bytes are not representing a ActionRequestNormal. Action type "
                f"is {request_type}"
            )
        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )
        cosem_method = cosem.CosemMethod.from_bytes(data[:9])
        data = data[9:]

        # Check for access selection
        has_access_selection = bool(data.pop(0))
        access_selection = None
        if has_access_selection:
            # Parse access selection descriptor
            access_selection = AccessDescriptorFactory.from_bytes(bytes(data))
            # Move data pointer past the access selection
            access_len = len(access_selection.to_bytes())
            data = data[access_len:]

        # Check for data
        has_data = bool(data.pop(0))
        if has_data:
            request_data = bytes(data)
        else:
            request_data = None

        return cls(
            cosem_method=cosem_method,
            data=request_data,
            invoke_id_and_priority=invoke_id_and_priority,
            access_selection=access_selection,
        )


@attr.s(auto_attribs=True)
class ActionRequestWithFirstPblock(AbstractXDlmsApdu):
    """
    Action-Request-With-First-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    cosem-method           Cosem-Method,
    datablock              DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 195
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.WITH_FIRST_PBLOCK

    cosem_method: cosem.CosemMethod = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemMethod)
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.cosem_method.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not the correct tag for an ActionRequest, should "
                f"be {cls.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))

        if request_type != enumerations.ActionType.WITH_FIRST_PBLOCK:
            raise ValueError(
                f"Bytes are not representing a ActionRequestWithFirstPblock. Action type "
                f"is {request_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # CosemMethod (9 bytes)
        cosem_method = cosem.CosemMethod.from_bytes(bytes(data[:9]))
        data = data[9:]

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")
        data = data[4:]

        # raw-data (OCTET STRING)
        data_length, remaining = dlms_data.decode_variable_integer(bytes(data))
        data_block = bytes(remaining[:data_length])

        return cls(
            cosem_method=cosem_method,
            invoke_id_and_priority=invoke_id_and_priority,
            last_block=last_block,
            block_number=block_number,
            data_block=data_block,
        )


@attr.s(auto_attribs=True)
class ActionRequestNextPblock(AbstractXDlmsApdu):
    """
    Action-Request-Next-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    block-number            Unsigned32
    }
    """

    TAG: ClassVar[int] = 195
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NEXT_PBLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    block_number: int = attr.ib(default=0)

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.extend(self.block_number.to_bytes(4, "big"))
        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not the correct tag for an ActionRequest, should "
                f"be {cls.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))

        if request_type != enumerations.ActionType.NEXT_PBLOCK:
            raise ValueError(
                f"Bytes are not representing a ActionRequestNextPblock. Action type "
                f"is {request_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        block_number = int.from_bytes(bytes(data), "big")

        return cls(
            invoke_id_and_priority=invoke_id_and_priority,
            block_number=block_number,
        )


@attr.s(auto_attribs=True)
class CosemMethodWithSelectiveAccess:
    """
    Cosem-Method-With-Selective-Access ::= SEQUENCE
    {
    cosem-method  Cosem-Method,
    access-select [0] IMPLICIT Selective-Access-Descriptor OPTIONAL
    }
    """

    cosem_method: cosem.CosemMethod = attr.ib(
        validator=attr.validators.instance_of(cosem.CosemMethod)
    )
    access_selection: Optional[
        Union[
            "dlms_cosem.cosem.selective_access.RangeDescriptor",
            "dlms_cosem.cosem.selective_access.EntryDescriptor",
        ]
    ] = attr.ib(default=None)

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.extend(self.cosem_method.to_bytes())
        if self.access_selection:
            out.append(0x01)  # Has access selection
            access_bytes = self.access_selection.to_bytes()
            out.extend(access_bytes)
        else:
            out.append(0x00)  # No access selection
        return bytes(out)

    @classmethod
    def from_bytes(cls, data: bytearray) -> "CosemMethodWithSelectiveAccess":
        # Parse CosemMethod (9 bytes)
        cosem_method = cosem.CosemMethod.from_bytes(bytes(data[:9]))
        del data[:9]

        # Check for access selection
        has_access = bool(data.pop(0))
        access_selection = None
        if has_access:
            # Parse access selection descriptor
            access_selection = AccessDescriptorFactory.from_bytes(bytes(data))
            # Move data pointer past the access selection
            access_len = len(access_selection.to_bytes())
            del data[:access_len]

        return cls(
            cosem_method=cosem_method,
            access_selection=access_selection,
        )


@attr.s(auto_attribs=True)
class ActionRequestWithList(AbstractXDlmsApdu):
    """
    Action-Request-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    method-list           SEQUENCE OF Cosem-Method-With-Selective-Access
    }

    Cosem-Method-With-Selective-Access ::= SEQUENCE
    {
    cosem-method  Cosem-Method,
    access-select [0] IMPLICIT Selective-Access-Descriptor OPTIONAL
    }
    """

    TAG: ClassVar[int] = 195
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.WITH_LIST

    method_list: List[CosemMethodWithSelectiveAccess] = attr.ib(
        factory=list,
        converter=lambda v: [
            CosemMethodWithSelectiveAccess(m) if isinstance(m, cosem.CosemMethod) else m
            for m in (v or [])
        ],
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(len(self.method_list))

        for method_with_access in self.method_list:
            out.extend(method_with_access.to_bytes())

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not the correct tag for an ActionRequest, should "
                f"be {cls.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))

        if request_type != enumerations.ActionType.WITH_LIST:
            raise ValueError(
                f"Bytes are not representing a ActionRequestWithList. Action type "
                f"is {request_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of methods
        num_methods = data.pop(0)

        method_list = []
        for _ in range(num_methods):
            method_with_access = CosemMethodWithSelectiveAccess.from_bytes(data)
            method_list.append(method_with_access)

        return cls(
            method_list=method_list,
            invoke_id_and_priority=invoke_id_and_priority,
        )


@attr.s(auto_attribs=True)
class ActionRequestWithListAndFirstPblock(AbstractXDlmsApdu):
    """
    Action-Request-With-List-And-First-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    method-list           SEQUENCE OF Cosem-Method-With-Selective-Access,
    datablock              DataBlock-SA
    }
    """

    TAG: ClassVar[int] = 195
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.WITH_LIST_AND_FIRST_PBLOCK

    method_list: List[CosemMethodWithSelectiveAccess] = attr.ib(
        factory=list,
        converter=lambda v: [
            CosemMethodWithSelectiveAccess(m) if isinstance(m, cosem.CosemMethod) else m
            for m in (v or [])
        ],
    )
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(len(self.method_list))

        # Method list with selective access
        for method_with_access in self.method_list:
            out.extend(method_with_access.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not the correct tag for an ActionRequest, should "
                f"be {cls.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))

        if request_type != enumerations.ActionType.WITH_LIST_AND_FIRST_PBLOCK:
            raise ValueError(
                f"Bytes are not representing a ActionRequestWithListAndFirstPblock. Action type "
                f"is {request_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # Number of methods
        num_methods = data.pop(0)

        method_list = []
        for _ in range(num_methods):
            method_with_access = CosemMethodWithSelectiveAccess.from_bytes(data)
            method_list.append(method_with_access)

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")
        data = data[4:]

        # raw-data (OCTET STRING)
        data_length, remaining = dlms_data.decode_variable_integer(bytes(data))
        data_block = bytes(remaining[:data_length])

        return cls(
            method_list=method_list,
            invoke_id_and_priority=invoke_id_and_priority,
            last_block=last_block,
            block_number=block_number,
            data_block=data_block,
        )


@attr.s(auto_attribs=True)
class ActionRequestFactory:
    """
    Factory that will parse the ActionRequest and return the correct class for the
    particular instance
    """

    TAG: ClassVar[int] = 195

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != ActionRequestFactory.TAG:
            raise ValueError(
                f"Tag for GET request is not correct. Got {tag}, should be "
                f"{ActionRequestFactory.TAG}"
            )
        request_type = enumerations.ActionType(data.pop(0))
        if request_type == enumerations.ActionType.NORMAL:
            return ActionRequestNormal.from_bytes(source_bytes)
        elif request_type == enumerations.ActionType.NEXT_PBLOCK:
            return ActionRequestNextPblock.from_bytes(source_bytes)
        elif request_type == enumerations.ActionType.WITH_LIST:
            return ActionRequestWithList.from_bytes(source_bytes)
        elif request_type == enumerations.ActionType.WITH_FIRST_PBLOCK:
            return ActionRequestWithFirstPblock.from_bytes(source_bytes)
        elif request_type == enumerations.ActionType.WITH_LIST_AND_FIRST_PBLOCK:
            return ActionRequestWithListAndFirstPblock.from_bytes(source_bytes)
        else:
            raise ValueError(f"Unknown ActionType: {request_type}")


@attr.s(auto_attribs=True)
class ActionResponseNormal(AbstractXDlmsApdu):
    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NORMAL

    status: enumerations.ActionResultStatus
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True)
    )

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.status.value)
        out.extend(b"\x00")

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        if action_type != enumerations.ActionType.NORMAL:
            raise ValueError(
                f"Bytes are not representing a ActionResponseNormal. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        status = enumerations.ActionResultStatus(data.pop(0))
        has_data = bool(data.pop(0))
        if has_data:
            raise ValueError(
                f"ActionResponse has data and should not be a " f"ActionResponseNormal"
            )

        return cls(invoke_id_and_priority=invoke_id_and_priority, status=status)


@attr.s(auto_attribs=True)
class ActionResponseNormalWithData(AbstractXDlmsApdu):
    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NORMAL

    status: enumerations.ActionResultStatus
    data: bytes = attr.ib(default=None)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True)
    )

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.status.value)
        out.extend(b"\x01")  # has data
        out.extend(b"\x00")  # data result choice
        out.extend(self.data)
        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        if action_type != enumerations.ActionType.NORMAL:
            raise ValueError(
                f"Bytes are not representing a ActionResponseNormal. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        status = enumerations.ActionResultStatus(data.pop(0))
        has_data = bool(data.pop(0))
        if has_data:
            data_is_result = data.pop(0) == 0
            if not data_is_result:
                raise ValueError(
                    "Data is not a ActionResponseNormalWithData, maybe a "
                    "ActionResponseNormalWithError"
                )
            response_data = data

        else:
            raise ValueError(
                f"ActionResponseNormalWithData does not contain any data. "
                f"Should probably be an ActionResponseNormal"
            )

        return cls(
            invoke_id_and_priority=invoke_id_and_priority,
            status=status,
            data=response_data,
        )


@attr.s(auto_attribs=True)
class ActionResponseNormalWithError(AbstractXDlmsApdu):
    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NORMAL

    status: enumerations.ActionResultStatus
    error: enumerations.DataAccessResult
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True)
    )

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(self.status.value)

        out.extend(b"\x01")
        out.extend(b"\x01")  # data result data (error) choice
        out.append(self.error.value)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):

        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        if action_type != enumerations.ActionType.NORMAL:
            raise ValueError(
                f"Bytes are not representing a ActionResponseNormal. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        status = enumerations.ActionResultStatus(data.pop(0))
        has_data = bool(data.pop(0))
        if has_data:
            data_is_error = data.pop(0) == 1
            if not data_is_error:
                raise ValueError(
                    "Data is not a ActionResponseNormalWithError, maybe a "
                    "ActionResponseNormal"
                )
            assert len(data) == 1
            error = enumerations.DataAccessResult(data.pop(0))

        else:
            raise ValueError("No error data in ActionResponseWithError")

        return cls(
            invoke_id_and_priority=invoke_id_and_priority, status=status, error=error
        )


@attr.s(auto_attribs=True)
class ActionResponseWithPblock(AbstractXDlmsApdu):
    """
    Action-Response-With-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.WITH_PBLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        if action_type != enumerations.ActionType.WITH_PBLOCK:
            raise ValueError(
                f"Bytes are not representing a ActionResponseWithPblock. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")
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


@attr.s(auto_attribs=True)
class ActionResponseNextPblock(AbstractXDlmsApdu):
    """
    Action-Response-Next-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NEXT_PBLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=False)
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        if action_type != enumerations.ActionType.NEXT_PBLOCK:
            raise ValueError(
                f"Bytes are not representing a ActionResponseNextPblock. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")
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


@attr.s(auto_attribs=True)
class ActionResponseWithList(AbstractXDlmsApdu):
    """
    Action-Response-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    list-of-responses       SEQUENCE OF Action-Response-With-Optional-Data
    }

    Action-Response-With-Optional-Data ::= SEQUENCE
    {
    result              Action-Result,
    return-parameters   Get-Data-Result OPTIONAL
    }
    """

    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.WITH_LIST

    response_list: List[
        Union[
            Tuple[enumerations.ActionResultStatus, None],
            Tuple[enumerations.ActionResultStatus, bytes],
            Tuple[enumerations.ActionResultStatus, enumerations.DataAccessResult],
        ]
    ] = attr.ib(factory=list)
    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())
        out.append(len(self.response_list))

        for response in self.response_list:
            status, data = response
            out.append(status.value)
            if data is None:
                out.append(0x00)  # No data
            elif isinstance(data, bytes):
                out.append(0x01)  # Has data
                out.append(0x00)  # Data result choice
                out.extend(data)
            elif isinstance(data, enumerations.DataAccessResult):
                out.append(0x01)  # Has data
                out.append(0x01)  # Error result choice
                out.append(data.value)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag is not correct. Should be {ActionResponseFactory.TAG} but is {tag}"
            )
        response_type = enumerations.ActionType(data.pop(0))

        data.pop(0)  # Invoke id and priority that is not needed for parsing

        if response_type == enumerations.ActionType.WITH_LIST:
            # Number of responses
            num_responses = data.pop(0)

            response_list = []
            for _ in range(num_responses):
                status = enumerations.ActionResultStatus(data.pop(0))
                has_data = bool(data.pop(0))

                if not has_data:
                    response_list.append((status, None))
                else:
                    choice = data.pop(0)
                    if choice == 0:  # Data
                        # TODO: Parse the data
                        response_data = bytes(data)
                        response_list.append((status, response_data))
                        break
                    elif choice == 1:  # Error
                        error = enumerations.DataAccessResult(data.pop(0))
                        response_list.append((status, error))
                    else:
                        raise ValueError(f"Unknown choice: {choice}")

            return cls(
                invoke_id_and_priority=InvokeIdAndPriority.from_bytes(
                    bytes([0xC0 | (1 << 6) | (1 << 7)])
                ),
                response_list=response_list,
            )
        else:
            raise ValueError("Only implemented the ActionResponse Normal class types")


@attr.s(auto_attribs=True)
class ActionResponseLastPblock(AbstractXDlmsApdu):
    """
    Action-Response-Last-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    DataBlock-SA ::= SEQUENCE
    {
    last-block      BOOLEAN,
    block-number    Unsigned32,
    raw-data        OCTET STRING
    }
    """

    TAG: ClassVar[int] = 199
    ACTION_TYPE: ClassVar[enumerations.ActionType] = enumerations.ActionType.NEXT_PBLOCK

    invoke_id_and_priority: InvokeIdAndPriority = attr.ib(
        default=InvokeIdAndPriority(0, True, True),
        validator=attr.validators.instance_of(InvokeIdAndPriority),
    )
    last_block: bool = attr.ib(default=True)  # Always last block
    block_number: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self):
        out = bytearray()
        out.append(self.TAG)
        out.append(self.ACTION_TYPE.value)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # DataBlock-SA
        out.append(0x01 if self.last_block else 0x00)
        out.extend(self.block_number.to_bytes(4, "big"))
        out.extend(dlms_data.encode_variable_integer(len(self.data_block)))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag {tag} is not correct for ActionResponse. Should be {cls.TAG}"
            )
        action_type = enumerations.ActionType(data.pop(0))

        # Note: The ActionType enum doesn't have LAST_PBLOCK separately
        # We use NEXT_PBLOCK and check the last_block field
        if action_type not in (
            enumerations.ActionType.NEXT_PBLOCK,
            enumerations.ActionType.WITH_PBLOCK,
        ):
            raise ValueError(
                f"Bytes are not representing a ActionResponseLastPblock. Action type "
                f"is {action_type}"
            )

        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(
            data.pop(0).to_bytes(1, "big")
        )

        # DataBlock-SA
        last_block = bool(data.pop(0))
        block_number = int.from_bytes(bytes(data[:4]), "big")
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


@attr.s(auto_attribs=True)
class ActionResponseFactory:

    """
    Action-Response ::= CHOICE
    {
    action-response-normal      [1] IMPLICIT Action-Response-Normal,
    action-response-with-pblock [2] IMPLICIT Action-Response-With-Pblock,
    action-response-next-pblock [3] IMPLICIT Action-Response-Next-Pblock,
    action-response-with-list   [4] IMPLICIT Action-Response-With-List,
    action-response-last-pblock [5] IMPLICIT Action-Response-Last-Pblock,
    }

    Action-Response-Normal ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    single-response         Action-Response-With-Optional-Data
    }

    Action-Response-With-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    Action-Response-Next-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    Action-Response-With-List ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    list-of-responses       SEQUENCE OF Action-Response-With-Optional-Data
    }

    Action-Response-Last-Pblock ::= SEQUENCE
    {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    pblock                  DataBlock-SA
    }

    Action-Response-With-Optional-Data ::= SEQUENCE
    {
    result              Action-Result,
    return-parameters   Get-Data-Result OPTIONAL
    }

    Get-Data-Result ::= CHOICE
    {
    data                [0] Data,
    ata-access-result   [1] IMPLICIT Data-Access-Result
    }

    """

    TAG: ClassVar[int] = 199

    @staticmethod
    def from_bytes(source_bytes: bytes):
        data = bytearray(source_bytes)
        tag = data.pop(0)
        if tag != ActionResponseFactory.TAG:
            raise ValueError(
                f"Tag is not correct. Should be {ActionResponseFactory.TAG} but is {tag}"
            )
        response_type = enumerations.ActionType(data.pop(0))

        data.pop(0)  # Invoke id and priority that is not needed for parsing

        if response_type == enumerations.ActionType.NORMAL:
            # check if it is an error or data response by assesing the choice.
            status = enumerations.ActionResultStatus(data.pop(0))
            has_data = bool(data.pop(0))
            if has_data:
                choice = data.pop(0)
                if choice == 0:  # Data
                    # Create ActionResponseNormalWithData directly
                    return ActionResponseNormalWithData(
                        invoke_id_and_priority=InvokeIdAndPriority.from_bytes(
                            bytes([0xC0 | (1 << 6) | (1 << 7)])
                        ),
                        status=status,
                        data=bytes(data),
                    )
                elif choice == 1:  # Error
                    error = enumerations.DataAccessResult(data.pop(0))
                    return ActionResponseNormalWithError(
                        invoke_id_and_priority=InvokeIdAndPriority.from_bytes(
                            bytes([0xC0 | (1 << 6) | (1 << 7)])
                        ),
                        status=status,
                        error=error,
                    )
            else:
                # No data
                return ActionResponseNormal(
                    invoke_id_and_priority=InvokeIdAndPriority.from_bytes(
                        bytes([0xC0 | (1 << 6) | (1 << 7)])
                    ),
                    status=status,
                )
        elif response_type == enumerations.ActionType.WITH_PBLOCK:
            return ActionResponseWithPblock.from_bytes(source_bytes)
        elif response_type == enumerations.ActionType.NEXT_PBLOCK:
            return ActionResponseNextPblock.from_bytes(source_bytes)
        elif response_type == enumerations.ActionType.WITH_LIST:
            return ActionResponseWithList.from_bytes(source_bytes)
        # Note: LAST_PBLOCK is not a separate enum value, it uses NEXT_PBLOCK or WITH_PBLOCK
        # and the last_block field in the DataBlock-SA structure determines if it's the last block
        else:
            raise NotImplementedError(
                "Only implemented the ActionResponse Normal "
                "class types is not implemented."
            )
