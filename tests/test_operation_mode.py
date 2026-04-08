"""
Tests for operation modes (Green Book 6.2-6.3).
"""
import pytest
from dlms_cosem.operation_mode import (
    OperationMode,
    OperationModeError,
    check_write_permission,
    switch_mode,
    validate_operation,
)


def test_operation_mode_allows_write():
    """Test write permission for different operation modes."""
    assert OperationMode.READOUT.allows_write() is False
    assert OperationMode.PROGRAMMING.allows_write() is True


def test_operation_mode_allows_read():
    """Test read permission for different operation modes."""
    assert OperationMode.READOUT.allows_read() is True
    assert OperationMode.PROGRAMMING.allows_read() is True


def test_check_write_permission_readout():
    """Test that write operations fail in readout mode."""
    with pytest.raises(OperationModeError) as exc_info:
        check_write_permission(OperationMode.READOUT)
    assert "Write operations not allowed" in str(exc_info.value)


def test_check_write_permission_programming():
    """Test that write operations succeed in programming mode."""
    # Should not raise any exception
    check_write_permission(OperationMode.PROGRAMMING)


def test_switch_mode():
    """Test switching between operation modes."""
    new_mode = switch_mode(OperationMode.READOUT, OperationMode.PROGRAMMING)
    assert new_mode == OperationMode.PROGRAMMING


def test_validate_operation_read():
    """Test validating read operations."""
    # Read should be allowed in both modes
    validate_operation(OperationMode.READOUT, "read")
    validate_operation(OperationMode.PROGRAMMING, "read")


def test_validate_operation_write():
    """Test validating write operations."""
    # Write should fail in readout mode
    with pytest.raises(OperationModeError):
        validate_operation(OperationMode.READOUT, "write")

    # Write should succeed in programming mode
    validate_operation(OperationMode.PROGRAMMING, "write")


def test_validate_operation_unknown():
    """Test validating unknown operation type."""
    with pytest.raises(ValueError) as exc_info:
        validate_operation(OperationMode.READOUT, "unknown")
    assert "Unknown operation type" in str(exc_info.value)
