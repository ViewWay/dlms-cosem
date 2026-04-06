"""
Block transfer support for DLMS/COSEM (Green Book 9.4.6/9.5/9.6).

This module implements block transfer for GET, NEXT, ACTION, and data transmission using blocks.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BlockTransferState(Enum):
    """Block transfer state machine states"""
    IDLE = 0
    TRANSMITTING = 1
    LAST_BLOCK_RECEIVED = 2
    BLOCK_RECEIVED = 3
    WAITING_FOR_NEXT_BLOCK = 4
    ERROR = 5
    TIMEOUT = 6
    COMPLETE = 7


@dataclass
class Block:
    """A single data block in block transfer"""
    block_number: int
    data: bytes
    is_last_block: bool


class BlockTransferError(Exception):
    """Exception raised during block transfer operations"""
    pass


@dataclass
class BlockTransfer:
    """Block transfer manager for DLMS/COSEM"""
    
    state: BlockTransferState = field(default_factory=lambda: BlockTransferState.IDLE)
    current_block_number: int = 0
    received_blocks: List[Block] = field(default_factory=list)
    is_complete: bool = False
    total_expected_length: Optional[int] = None
    timeout_ms: int = 5000  # 5 second default timeout
    
    def reset(self) -> None:
        """Reset transfer state"""
        self.state = BlockTransferState.IDLE
        self.current_block_number = 0
        self.received_blocks.clear()
        self.is_complete = False
        self.total_expected_length = None
    
    def start_transfer(self, expected_length: Optional[int] = None) -> None:
        """Start a new block transfer"""
        if self.state != BlockTransferState.IDLE:
            raise BlockTransferError(f"Cannot start transfer in state {self.state}")
        
        self.state = BlockTransferState.TRANSMITTING
        self.current_block_number = 0
        self.is_complete = False
        self.total_expected_length = expected_length
    
    def add_block(self, block: Block) -> None:
        """Add a received block"""
        if self.state not in (BlockTransferState.TRANSMITTING, BlockTransferState.WAITING_FOR_NEXT_BLOCK):
            raise BlockTransferError(f"Cannot add block in state {self.state}")
        
        if block.block_number != self.current_block_number:
            raise BlockTransferError(
                f"Expected block {self.current_block_number}, got {block.block_number}"
            )
        
        self.received_blocks.append(block)
        self.current_block_number += 1
        
        if block.is_last_block:
            self.state = BlockTransferState.COMPLETE
            self.is_complete = True
        else:
            self.state = BlockTransferState.WAITING_FOR_NEXT_BLOCK
    
    def get_data(self) -> Optional[bytes]:
        """Get reassembled data if transfer is complete"""
        if not self.is_complete:
            return None
        
        return b''.join(block.data for block in self.received_blocks)
    
    def get_block(self, block_number: int) -> Optional[Block]:
        """Get a specific block by block number"""
        for block in self.received_blocks:
            if block.block_number == block_number:
                return block
        return None
    
    def reassemble(self) -> bytes:
        """Reassemble all received blocks into complete data"""
        if not self.is_complete:
            raise BlockTransferError("Cannot reassemble incomplete block transfer")
        
        return b''.join(block.data for block in self.received_blocks)
    
    def get_total_transmitted(self) -> int:
        """Get total number of transmitted blocks"""
        return len(self.received_blocks)
    
    def get_progress(self) -> dict:
        """Get transfer progress"""
        return {
            "state": self.state.name,
            "current_block": self.current_block_number,
            "total_blocks": len(self.received_blocks),
            "is_complete": self.is_complete,
        }
    
    def validate_sequence_numbers(self) -> None:
        """Validate that block sequence numbers are correct"""
        expected_number = 0
        for block in self.received_blocks:
            if block.block_number != expected_number:
                raise BlockTransferError(
                    f"Block sequence error: expected {expected_number}, got {block.block_number}"
                )
            expected_number += 1
