"""
Unit tests for General Block Transfer functionality.
"""

import pytest

from dlms_cosem.protocol.xdlms.general_block_transfer import (
    BlockTransferStatus,
    BlockType,
    GeneralBlockTransferRequest,
    GeneralBlockTransferResponse,
)
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority


class TestBlockType:
    """Tests for BlockType constants."""

    def test_block_type_constants(self):
        """Test that block type constants have correct values."""
        assert BlockType.LAST_BLOCK_NO_ERROR == 0b00000000
        assert BlockType.LAST_BLOCK_WITH_ERROR == 0b00001000
        assert BlockType.FIRST_BLOCK == 0b00011000
        assert BlockType.INTERMEDIATE_BLOCK == 0b00011100


class TestGeneralBlockTransferRequest:
    """Tests for GeneralBlockTransferRequest APDU."""

    def test_create_first_block(self):
        """Test creating a first block request."""
        invoke_id = InvokeIdAndPriority(invoke_id=1, confirmed=True, high_priority=False)
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=0,
            block_type_security=BlockType.FIRST_BLOCK,
            last_block=False,
            block_control=0,
            data_block=b"test data",
        )

        assert block.block_number == 0
        assert block.is_first_block
        assert not block.is_last_block_no_error
        assert not block.is_last_block_with_error
        assert not block.is_intermediate_block
        assert not block.is_ciphered
        assert not block.is_acknowledged

    def test_create_intermediate_block(self):
        """Test creating an intermediate block request."""
        invoke_id = InvokeIdAndPriority(invoke_id=2)
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=1,
            block_type_security=BlockType.INTERMEDIATE_BLOCK,
            last_block=False,
            data_block=b"more data",
        )

        assert block.block_number == 1
        assert block.is_intermediate_block
        assert not block.is_first_block
        assert not block.last_block

    def test_create_last_block(self):
        """Test creating a last block request."""
        invoke_id = InvokeIdAndPriority(invoke_id=3)
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=2,
            block_type_security=BlockType.LAST_BLOCK_NO_ERROR,
            last_block=True,
            data_block=b"final data",
        )

        assert block.block_number == 2
        assert block.is_last_block_no_error
        assert block.last_block
        assert not block.is_first_block
        assert not block.is_intermediate_block

    def test_encode_decode_first_block(self):
        """Test encoding and decoding a first block."""
        invoke_id = InvokeIdAndPriority(invoke_id=5)
        original = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=0,
            block_type_security=BlockType.FIRST_BLOCK,
            last_block=False,
            data_block=b"Hello, World!",
        )

        encoded = original.to_bytes()
        decoded = GeneralBlockTransferRequest.from_bytes(encoded)

        assert decoded.invoke_id_and_priority.invoke_id == 5
        assert decoded.block_number == 0
        assert decoded.is_first_block
        assert not decoded.last_block
        assert decoded.data_block == b"Hello, World!"

    def test_encode_decode_last_block(self):
        """Test encoding and decoding a last block."""
        invoke_id = InvokeIdAndPriority(invoke_id=10)
        original = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=5,
            block_type_security=BlockType.LAST_BLOCK_NO_ERROR,
            last_block=True,
            data_block=b"Final block data",
        )

        encoded = original.to_bytes()
        decoded = GeneralBlockTransferRequest.from_bytes(encoded)

        assert decoded.invoke_id_and_priority.invoke_id == 10
        assert decoded.block_number == 5
        assert decoded.is_last_block_no_error
        assert decoded.last_block
        assert decoded.data_block == b"Final block data"

    def test_encode_decode_large_data_block(self):
        """Test encoding and decoding with large data block."""
        large_data = b"X" * 1000
        invoke_id = InvokeIdAndPriority(invoke_id=7)
        original = GeneralBlockTransferRequest(
            invoke_id_and_priority=invoke_id,
            block_number=3,
            block_type_security=BlockType.INTERMEDIATE_BLOCK,
            last_block=False,
            data_block=large_data,
        )

        encoded = original.to_bytes()
        decoded = GeneralBlockTransferRequest.from_bytes(encoded)

        assert decoded.block_number == 3
        assert decoded.is_intermediate_block
        assert len(decoded.data_block) == 1000
        assert decoded.data_block == large_data

    def test_ciphered_block(self):
        """Test creating a ciphered block."""
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            block_number=0,
            block_type_security=BlockType.FIRST_BLOCK | 0b00000010,  # Set ciphered bit
            last_block=False,
            data_block=b"encrypted data",
        )

        assert block.is_ciphered

    def test_acknowledged_block(self):
        """Test creating an acknowledged block."""
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            block_number=0,
            block_type_security=BlockType.FIRST_BLOCK | 0b00000001,  # Set acknowledged bit
            last_block=False,
            data_block=b"data",
        )

        assert block.is_acknowledged

    def test_block_with_error(self):
        """Test creating a block with error."""
        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            block_number=10,
            block_type_security=BlockType.LAST_BLOCK_WITH_ERROR,
            last_block=True,
            block_control=0b00010000,  # Error code 1
            data_block=b"",
        )

        assert block.is_last_block_with_error
        assert block.error_code == 1

    def test_invalid_tag_raises_error(self):
        """Test that invalid tag raises ValueError."""
        invalid_data = bytes([0xFF, 0x01, 0, 0, 0, 0, 0, 0, 0, 0x01, 0x00])

        with pytest.raises(ValueError, match="Tag for General Block Transfer Request"):
            GeneralBlockTransferRequest.from_bytes(invalid_data)


class TestGeneralBlockTransferResponse:
    """Tests for GeneralBlockTransferResponse APDU."""

    def test_create_response(self):
        """Test creating a block transfer response."""
        invoke_id = InvokeIdAndPriority(invoke_id=1)
        response = GeneralBlockTransferResponse(
            invoke_id_and_priority=invoke_id,
            block_number=0,
            last_block=False,
            block_control=0,
            data_block=b"response data",
        )

        assert response.block_number == 0
        assert not response.last_block
        assert not response.has_error
        assert response.error_code is None

    def test_encode_decode_response(self):
        """Test encoding and decoding a response."""
        invoke_id = InvokeIdAndPriority(invoke_id=3)
        original = GeneralBlockTransferResponse(
            invoke_id_and_priority=invoke_id,
            block_number=2,
            last_block=True,
            block_control=0,
            data_block=b"complete response",
        )

        encoded = original.to_bytes()
        decoded = GeneralBlockTransferResponse.from_bytes(encoded)

        assert decoded.invoke_id_and_priority.invoke_id == 3
        assert decoded.block_number == 2
        assert decoded.last_block
        assert decoded.data_block == b"complete response"

    def test_response_with_error(self):
        """Test a response indicating an error."""
        response = GeneralBlockTransferResponse(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            block_number=0,
            last_block=True,
            block_control=0b00100000,  # Error code 2
            data_block=b"",
        )

        assert response.has_error
        assert response.error_code == 2

    def test_invalid_tag_raises_error(self):
        """Test that invalid tag raises ValueError."""
        invalid_data = bytes([0xFF, 0x01, 0, 0, 0, 0, 0x01, 0x00])

        with pytest.raises(ValueError, match="Tag for General Block Transfer Response"):
            GeneralBlockTransferResponse.from_bytes(invalid_data)


class TestBlockTransferStatus:
    """Tests for BlockTransferStatus state management."""

    def test_initial_state(self):
        """Test initial state of block transfer status."""
        status = BlockTransferStatus()

        assert status.current_block_number == 0
        assert status.total_blocks == 0
        assert len(status.received_data) == 0
        assert not status.is_complete
        assert status.error is None

    def test_add_first_block(self):
        """Test adding the first block."""
        status = BlockTransferStatus()
        status.add_block_data(b"block 0", block_number=0, is_last=False)

        assert status.current_block_number == 1
        assert bytes(status.received_data) == b"block 0"
        assert not status.is_complete

    def test_add_multiple_blocks(self):
        """Test adding multiple blocks in sequence."""
        status = BlockTransferStatus()
        status.add_block_data(b"block 0", block_number=0, is_last=False)
        status.add_block_data(b"block 1", block_number=1, is_last=False)
        status.add_block_data(b"block 2", block_number=2, is_last=True)

        assert status.current_block_number == 3
        assert bytes(status.received_data) == b"block 0block 1block 2"
        assert status.is_complete

    def test_add_block_out_of_sequence_raises_error(self):
        """Test that adding blocks out of sequence raises ValueError."""
        status = BlockTransferStatus()
        status.add_block_data(b"block 0", block_number=0, is_last=False)

        with pytest.raises(ValueError, match="Block number mismatch"):
            status.add_block_data(b"block 2", block_number=2, is_last=False)

    def test_reset(self):
        """Test resetting the block transfer status."""
        status = BlockTransferStatus()
        status.add_block_data(b"data", block_number=0, is_last=False)
        status.total_blocks = 5

        status.reset()

        assert status.current_block_number == 0
        assert status.total_blocks == 0
        assert len(status.received_data) == 0
        assert not status.is_complete
        assert status.error is None

    def test_set_error(self):
        """Test setting an error state."""
        status = BlockTransferStatus()
        status.set_error("Transfer failed")

        assert status.error == "Transfer failed"
        assert status.is_complete

    def test_block_number_mismatch_after_reset(self):
        """Test that after reset, block numbers start from 0."""
        status = BlockTransferStatus()
        status.add_block_data(b"data", block_number=0, is_last=False)
        status.reset()

        # Should accept block 0 again after reset
        status.add_block_data(b"new data", block_number=0, is_last=True)
        assert bytes(status.received_data) == b"new data"


class TestBlockTransferIntegration:
    """Integration tests for block transfer scenarios."""

    def test_split_and_reassemble_large_data(self):
        """Test splitting large data into blocks and reassembling."""
        # Simulate a large APDU that needs to be split
        large_data = b"This is a large APDU that needs to be split into multiple blocks." * 10

        # Simulate splitting into blocks
        block_size = 50
        blocks = []
        for i in range(0, len(large_data), block_size):
            chunk = large_data[i:i + block_size]
            is_last = (i + block_size) >= len(large_data)

            if i == 0:
                block_type = BlockType.FIRST_BLOCK
            elif is_last:
                block_type = BlockType.LAST_BLOCK_NO_ERROR
            else:
                block_type = BlockType.INTERMEDIATE_BLOCK

            block = GeneralBlockTransferRequest(
                invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
                block_number=len(blocks),
                block_type_security=block_type,
                last_block=is_last,
                data_block=chunk,
            )
            blocks.append(block)

        # Verify blocks were created correctly
        assert len(blocks) > 1
        assert blocks[0].is_first_block
        assert blocks[-1].is_last_block_no_error

        # Simulate receiving and reassembling
        status = BlockTransferStatus()
        for block in blocks:
            status.add_block_data(
                block.data_block,
                block.block_number,
                block.last_block,
            )

        # Verify reassembly
        assert status.is_complete
        assert bytes(status.received_data) == large_data

    def test_single_block_no_split_needed(self):
        """Test that small data doesn't need block transfer."""
        small_data = b"Small APDU"

        block = GeneralBlockTransferRequest(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            block_number=0,
            block_type_security=BlockType.LAST_BLOCK_NO_ERROR,
            last_block=True,
            data_block=small_data,
        )

        status = BlockTransferStatus()
        status.add_block_data(block.data_block, block.block_number, block.last_block)

        assert status.is_complete
        assert bytes(status.received_data) == small_data
