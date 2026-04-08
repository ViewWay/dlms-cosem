"""
General Block Transfer APDU implementation.

According to DLMS Green Book, the General Block Transfer service allows
transferring large amounts of data that exceed the maximum PDU size.

General-Block-Transfer ::= CHOICE {
    general-block-transfer-request  [0] IMPLICIT General-Block-Transfer-Request,
    general-block-transfer-response [1] IMPLICIT General-Block-Transfer-Response
}

General-Block-Transfer-Request ::= SEQUENCE {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    block-number            Unsigned32,
    block-type-security     OCTET STRING (SIZE(1)),
    last-block              BOOLEAN,
    block-control           OCTET STRING (SIZE(1)),
    data-block              OCTET STRING
}

General-Block-Transfer-Response ::= SEQUENCE {
    invoke-id-and-priority  Invoke-Id-And-Priority,
    block-number            Unsigned32,
    last-block              BOOLEAN,
    block-control           OCTET STRING (SIZE(1)),
    data-block              OCTET STRING
}

Block-Type-Security:
    Bit 0: Request acknowledged (0=No, 1=Yes)
    Bit 1: Ciphered (0=No, 1=Yes)
    Bit 2-3: Reserved
    Bit 4-6: Block type
        000 = Last block, no error
        001 = Last block with error
        010 = First block
        011 = Intermediate block
    Bit 7: Reserved

Block-Control:
    Bit 0-3: Reserved
    Bit 4-7: Error code (if last block with error)
"""

from typing import *

import attr

from dlms_cosem.dlms_data import decode_variable_integer, encode_variable_integer
from dlms_cosem.protocol.xdlms.base import AbstractXDlmsApdu
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority


class BlockType:
    """Block type values for Block-Type-Security field."""

    LAST_BLOCK_NO_ERROR = 0b00000000
    LAST_BLOCK_WITH_ERROR = 0b00001000
    FIRST_BLOCK = 0b00011000
    INTERMEDIATE_BLOCK = 0b00011100


@attr.s(auto_attribs=True)
class GeneralBlockTransferRequest(AbstractXDlmsApdu):
    """
    General Block Transfer Request APDU.

    Used to transfer large data blocks when the data exceeds the maximum PDU size.
    """

    TAG: ClassVar[int] = 0x10  # general-block-transfer-request choice

    invoke_id_and_priority: InvokeIdAndPriority
    block_number: int = attr.ib(default=0)
    block_type_security: int = attr.ib(default=BlockType.FIRST_BLOCK)
    last_block: bool = attr.ib(default=False)
    block_control: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self) -> bytes:
        """Encode the General Block Transfer Request to bytes."""
        out = bytearray()

        # Tag (General Block Transfer Request)
        out.append(self.TAG)

        # Invoke-Id-And-Priority (1 byte)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # Block-Number (4 bytes, Unsigned32)
        out.extend(self.block_number.to_bytes(4, "big"))

        # Block-Type-Security (1 byte)
        out.append(self.block_type_security)

        # Last-Block (1 byte, BOOLEAN)
        out.append(0x01 if self.last_block else 0x00)

        # Block-Control (1 byte)
        out.append(self.block_control)

        # Data-Block (OCTET STRING with variable length)
        data_length = len(self.data_block)
        out.extend(encode_variable_integer(data_length))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes) -> "GeneralBlockTransferRequest":
        """Decode bytes into a General Block Transfer Request."""
        data = bytearray(source_bytes)

        # Tag
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for General Block Transfer Request should be {cls.TAG}, got {tag}"
            )

        # Invoke-Id-And-Priority
        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(bytes([data.pop(0)]))

        # Block-Number
        block_number_bytes = bytes(data[:4])
        block_number = int.from_bytes(block_number_bytes, "big")
        for _ in range(4):
            data.pop(0)

        # Block-Type-Security
        block_type_security = data.pop(0)

        # Last-Block
        last_block = bool(data.pop(0))

        # Block-Control
        block_control = data.pop(0)

        # Data-Block
        data_length, remaining_bytes = decode_variable_integer(bytes(data))
        data_block = bytes(remaining_bytes[:data_length])

        return cls(
            invoke_id_and_priority=invoke_id_and_priority,
            block_number=block_number,
            block_type_security=block_type_security,
            last_block=last_block,
            block_control=block_control,
            data_block=data_block,
        )

    @property
    def is_first_block(self) -> bool:
        """Check if this is the first block."""
        return (self.block_type_security & 0b00011100) == BlockType.FIRST_BLOCK

    @property
    def is_intermediate_block(self) -> bool:
        """Check if this is an intermediate block."""
        return (self.block_type_security & 0b00011100) == BlockType.INTERMEDIATE_BLOCK

    @property
    def is_last_block_no_error(self) -> bool:
        """Check if this is the last block without error."""
        return (
            self.last_block
            and (self.block_type_security & 0b00011100) == BlockType.LAST_BLOCK_NO_ERROR
        )

    @property
    def is_last_block_with_error(self) -> bool:
        """Check if this is the last block with error."""
        return (
            self.last_block
            and (self.block_type_security & 0b00011100)
            == BlockType.LAST_BLOCK_WITH_ERROR
        )

    @property
    def is_ciphered(self) -> bool:
        """Check if the block is ciphered."""
        return bool(self.block_type_security & 0b00000010)

    @property
    def is_acknowledged(self) -> bool:
        """Check if this is an acknowledged request."""
        return bool(self.block_type_security & 0b00000001)

    @property
    def error_code(self) -> Optional[int]:
        """Get the error code if this is a last block with error."""
        if self.is_last_block_with_error:
            return (self.block_control & 0b11110000) >> 4
        return None


@attr.s(auto_attribs=True)
class GeneralBlockTransferResponse(AbstractXDlmsApdu):
    """
    General Block Transfer Response APDU.

    Used by the server to respond to General Block Transfer Requests.
    """

    TAG: ClassVar[int] = 0x11  # general-block-transfer-response choice

    invoke_id_and_priority: InvokeIdAndPriority
    block_number: int = attr.ib(default=0)
    last_block: bool = attr.ib(default=False)
    block_control: int = attr.ib(default=0)
    data_block: bytes = attr.ib(default=b"")

    def to_bytes(self) -> bytes:
        """Encode the General Block Transfer Response to bytes."""
        out = bytearray()

        # Tag (General Block Transfer Response)
        out.append(self.TAG)

        # Invoke-Id-And-Priority (1 byte)
        out.extend(self.invoke_id_and_priority.to_bytes())

        # Block-Number (4 bytes, Unsigned32)
        out.extend(self.block_number.to_bytes(4, "big"))

        # Last-Block (1 byte, BOOLEAN)
        out.append(0x01 if self.last_block else 0x00)

        # Block-Control (1 byte)
        out.append(self.block_control)

        # Data-Block (OCTET STRING with variable length)
        data_length = len(self.data_block)
        out.extend(encode_variable_integer(data_length))
        out.extend(self.data_block)

        return bytes(out)

    @classmethod
    def from_bytes(cls, source_bytes: bytes) -> "GeneralBlockTransferResponse":
        """Decode bytes into a General Block Transfer Response."""
        data = bytearray(source_bytes)

        # Tag
        tag = data.pop(0)
        if tag != cls.TAG:
            raise ValueError(
                f"Tag for General Block Transfer Response should be {cls.TAG}, got {tag}"
            )

        # Invoke-Id-And-Priority
        invoke_id_and_priority = InvokeIdAndPriority.from_bytes(bytes([data.pop(0)]))

        # Block-Number
        block_number_bytes = bytes(data[:4])
        block_number = int.from_bytes(block_number_bytes, "big")
        for _ in range(4):
            data.pop(0)

        # Last-Block
        last_block = bool(data.pop(0))

        # Block-Control
        block_control = data.pop(0)

        # Data-Block
        data_length, remaining_bytes = decode_variable_integer(bytes(data))
        data_block = bytes(remaining_bytes[:data_length])

        return cls(
            invoke_id_and_priority=invoke_id_and_priority,
            block_number=block_number,
            last_block=last_block,
            block_control=block_control,
            data_block=data_block,
        )

    @property
    def has_error(self) -> bool:
        """Check if the response indicates an error."""
        # Error is indicated in block-control bits 4-7
        return (self.block_control & 0b11110000) != 0

    @property
    def error_code(self) -> Optional[int]:
        """Get the error code if present."""
        if self.has_error:
            return (self.block_control & 0b11110000) >> 4
        return None


@attr.s(auto_attribs=True)
class BlockTransferStatus:
    """
    State management for block transfer operations.

    Tracks the progress of multi-block transfers.
    """

    current_block_number: int = attr.ib(default=0)
    total_blocks: int = attr.ib(default=0)
    received_data: bytearray = attr.ib(factory=bytearray)
    is_complete: bool = attr.ib(default=False)
    error: Optional[str] = attr.ib(default=None)

    def reset(self):
        """Reset the block transfer status."""
        self.current_block_number = 0
        self.total_blocks = 0
        self.received_data = bytearray()
        self.is_complete = False
        self.error = None

    def add_block_data(self, data: bytes, block_number: int, is_last: bool = False):
        """
        Add data from a received block.

        Raises ValueError if block numbers are out of sequence.
        """
        if block_number != self.current_block_number:
            raise ValueError(
                f"Block number mismatch: expected {self.current_block_number}, "
                f"got {block_number}"
            )

        self.received_data.extend(data)
        self.current_block_number += 1

        if is_last:
            self.is_complete = True

    def set_error(self, error: str):
        """Mark the transfer as failed with an error."""
        self.error = error
        self.is_complete = True
