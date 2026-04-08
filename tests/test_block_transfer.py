"""
Tests for block transfer functionality according to Green Book.
"""
import pytest
from dlms_cosem.block_transfer import (
    Block,
    BlockTransfer,
    BlockTransferState,
    BlockTransferError,
)


class TestBlock:
    """Test Block dataclass"""
    
    def test_create_block(self):
        """Test creating a block"""
        block = Block(block_number=0, data=b"test", is_last_block=False)
        assert block.block_number == 0
        assert block.data == b"test"
        assert block.is_last_block is False
    
    def test_create_last_block(self):
        """Test creating a last block"""
        block = Block(block_number=2, data=b"final", is_last_block=True)
        assert block.block_number == 2
        assert block.is_last_block is True


class TestBlockTransfer:
    """Test BlockTransfer class"""
    
    def test_initial_state(self):
        """Test initial state"""
        bt = BlockTransfer()
        assert bt.state == BlockTransferState.IDLE
        assert bt.current_block_number == 0
        assert len(bt.received_blocks) == 0
        assert bt.is_complete is False
    
    def test_start_transfer(self):
        """Test starting a transfer"""
        bt = BlockTransfer()
        bt.start_transfer(expected_length=1000)
        
        assert bt.state == BlockTransferState.TRANSMITTING
        assert bt.current_block_number == 0
        assert bt.total_expected_length == 1000
        assert bt.is_complete is False
    
    def test_start_twice_fails(self):
        """Test that starting twice raises error"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        with pytest.raises(BlockTransferError):
            bt.start_transfer()
    
    def test_add_single_block(self):
        """Test adding a single block that is also last"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        block = Block(block_number=0, data=b"hello", is_last_block=True)
        bt.add_block(block)
        
        assert bt.state == BlockTransferState.COMPLETE
        assert bt.is_complete is True
        assert len(bt.received_blocks) == 1
    
    def test_add_multiple_blocks(self):
        """Test adding multiple blocks"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        block1 = Block(block_number=0, data=b"part1", is_last_block=False)
        bt.add_block(block1)
        
        assert bt.state == BlockTransferState.WAITING_FOR_NEXT_BLOCK
        assert bt.current_block_number == 1
        
        block2 = Block(block_number=1, data=b"part2", is_last_block=True)
        bt.add_block(block2)
        
        assert bt.state == BlockTransferState.COMPLETE
        assert bt.is_complete is True
        assert len(bt.received_blocks) == 2
    
    def test_add_block_wrong_number_fails(self):
        """Test that adding block with wrong number raises error"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        block = Block(block_number=5, data=b"test", is_last_block=False)
        
        with pytest.raises(BlockTransferError, match="Expected block 0, got 5"):
            bt.add_block(block)
    
    def test_add_block_in_wrong_state_fails(self):
        """Test that adding block in IDLE state raises error"""
        bt = BlockTransfer()
        
        block = Block(block_number=0, data=b"test", is_last_block=True)
        
        with pytest.raises(BlockTransferError, match="Cannot add block in state"):
            bt.add_block(block)
    
    def test_reassemble_complete(self):
        """Test reassembling complete transfer"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        bt.add_block(Block(block_number=0, data=b"Hello ", is_last_block=False))
        bt.add_block(Block(block_number=1, data=b"World", is_last_block=True))
        
        result = bt.reassemble()
        assert result == b"Hello World"
    
    def test_reassemble_incomplete_fails(self):
        """Test that reassembling incomplete transfer raises error"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        bt.add_block(Block(block_number=0, data=b"part", is_last_block=False))
        
        with pytest.raises(BlockTransferError, match="Cannot reassemble incomplete"):
            bt.reassemble()
    
    def test_get_data_complete(self):
        """Test getting data from complete transfer"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        bt.add_block(Block(block_number=0, data=b"data1", is_last_block=False))
        bt.add_block(Block(block_number=1, data=b"data2", is_last_block=True))
        
        data = bt.get_data()
        assert data == b"data1data2"
    
    def test_get_data_incomplete(self):
        """Test getting data from incomplete transfer"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        bt.add_block(Block(block_number=0, data=b"part", is_last_block=False))
        
        data = bt.get_data()
        assert data is None
    
    def test_reset(self):
        """Test resetting transfer"""
        bt = BlockTransfer()
        bt.start_transfer()
        bt.add_block(Block(block_number=0, data=b"test", is_last_block=False))
        
        assert bt.state != BlockTransferState.IDLE
        assert len(bt.received_blocks) > 0
        
        bt.reset()
        
        assert bt.state == BlockTransferState.IDLE
        assert bt.current_block_number == 0
        assert len(bt.received_blocks) == 0
        assert bt.is_complete is False
    
    def test_validate_sequence_numbers_correct(self):
        """Test validating correct sequence numbers"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        bt.add_block(Block(block_number=0, data=b"a", is_last_block=False))
        bt.add_block(Block(block_number=1, data=b"b", is_last_block=False))
        bt.add_block(Block(block_number=2, data=b"c", is_last_block=True))
        
        # Should not raise
        bt.validate_sequence_numbers()
    
    def test_validate_sequence_numbers_incorrect(self):
        """Test validating incorrect sequence numbers"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        # Manually add blocks to test validation
        bt.received_blocks.append(Block(block_number=0, data=b"a", is_last_block=False))
        # Skip block 1
        bt.received_blocks.append(Block(block_number=2, data=b"c", is_last_block=True))
        
        with pytest.raises(BlockTransferError, match="Block sequence error"):
            bt.validate_sequence_numbers()
    
    def test_get_block(self):
        """Test getting a specific block"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        block1 = Block(block_number=0, data=b"first", is_last_block=False)
        block2 = Block(block_number=1, data=b"second", is_last_block=True)
        
        bt.add_block(block1)
        bt.add_block(block2)
        
        retrieved = bt.get_block(1)
        assert retrieved is not None
        assert retrieved.data == b"second"
    
    def test_get_nonexistent_block(self):
        """Test getting a block that doesn't exist"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        result = bt.get_block(5)
        assert result is None
    
    def test_get_total_transmitted(self):
        """Test getting total transmitted blocks"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        assert bt.get_total_transmitted() == 0
        
        bt.add_block(Block(block_number=0, data=b"a", is_last_block=False))
        assert bt.get_total_transmitted() == 1
        
        bt.add_block(Block(block_number=1, data=b"b", is_last_block=True))
        assert bt.get_total_transmitted() == 2
    
    def test_get_progress(self):
        """Test getting transfer progress"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        progress = bt.get_progress()
        assert progress["state"] == "TRANSMITTING"
        assert progress["current_block"] == 0
        assert progress["total_blocks"] == 0
        assert progress["is_complete"] is False
        
        bt.add_block(Block(block_number=0, data=b"test", is_last_block=True))
        
        progress = bt.get_progress()
        assert progress["state"] == "COMPLETE"
        assert progress["current_block"] == 1
        assert progress["total_blocks"] == 1
        assert progress["is_complete"] is True


class TestBlockTransferIntegration:
    """Integration tests for block transfer"""
    
    def test_large_data_split(self):
        """Test splitting large data into blocks"""
        bt = BlockTransfer()
        bt.start_transfer(expected_length=300)
        
        # Simulate splitting 300 bytes into 3 blocks
        block1 = Block(block_number=0, data=b"x" * 100, is_last_block=False)
        block2 = Block(block_number=1, data=b"y" * 100, is_last_block=False)
        block3 = Block(block_number=2, data=b"z" * 100, is_last_block=True)
        
        bt.add_block(block1)
        bt.add_block(block2)
        bt.add_block(block3)
        
        assert bt.is_complete
        result = bt.reassemble()
        assert len(result) == 300
        assert result == (b"x" * 100) + (b"y" * 100) + (b"z" * 100)
    
    def test_single_block_transfer(self):
        """Test transfer with single block (data fits in one block)"""
        bt = BlockTransfer()
        bt.start_transfer()
        
        block = Block(block_number=0, data=b"short data", is_last_block=True)
        bt.add_block(block)
        
        assert bt.is_complete
        assert bt.reassemble() == b"short data"
