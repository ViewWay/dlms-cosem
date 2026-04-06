"""
Operation modes for DLMS/COSEM (Green Book 6.2-6.3).

DLMS/COSEM defines two operation modes:
- Readout mode: Read-only access with HLS password authentication
- Programming mode: Read-write access with HLS-SLS signature authentication
"""
from enum import Enum


class OperationMode(Enum):
    """Operation mode for DLMS/COSEM connections."""

    READOUT = "readout"
    """Readout mode: Read-only access with HLS password authentication"""

    PROGRAMMING = "programming"
    """Programming mode: Read-write access with HLS-SLS signature authentication"""

    def allows_write(self) -> bool:
        """Check if write operations are allowed in this mode.

        Returns:
            bool: True if write operations are allowed, False otherwise.
        """
        return self == OperationMode.PROGRAMMING

    def allows_read(self) -> bool:
        """Check if read operations are allowed in this mode.

        Returns:
            bool: True (both modes allow read operations).
        """
        return True


class OperationModeError(Exception):
    """Exception raised when operation mode restrictions are violated."""

    def __init__(self, message: str):
        """Initialize operation mode error.

        Args:
            message: Error message describing the violation.
        """
        self.message = message
        super().__init__(self.message)


def check_write_permission(mode: OperationMode) -> None:
    """Check if write operations are allowed in the current mode.

    Args:
        mode: Current operation mode.

    Raises:
        OperationModeError: If write operations are not allowed in the current mode.
    """
    if not mode.allows_write():
        raise OperationModeError(
            f"Write operations not allowed in {mode.value} mode"
        )


def switch_mode(current_mode: OperationMode, new_mode: OperationMode) -> OperationMode:
    """Switch to a new operation mode.

    Args:
        current_mode: Current operation mode (unused, for API consistency).
        new_mode: New operation mode to switch to.

    Returns:
        OperationMode: The new operation mode.
    """
    return new_mode


def validate_operation(mode: OperationMode, operation: str) -> None:
    """Validate an operation against the current operation mode.

    Args:
        mode: Current operation mode.
        operation: Operation to validate ("read" or "write").

    Raises:
        OperationModeError: If the operation is not allowed in the current mode.
        ValueError: If the operation type is unknown.
    """
    if operation == "read":
        if not mode.allows_read():
            raise OperationModeError("Read operations not allowed")
    elif operation == "write":
        check_write_permission(mode)
    else:
        raise ValueError(f"Unknown operation type: {operation}")
