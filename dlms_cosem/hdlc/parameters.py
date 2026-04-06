"""
HDLC Parameter Negotiation for DLMS/COSEM.

This module implements the parameter negotiation mechanism defined in
DLMS UA 1000-3 Ed. 12 (White Book).

Parameters are encoded using TLV (Type-Length-Value) format in the
information field of SNRM and UA frames.
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Dict, List, Optional

import attr

from dlms_cosem.hdlc import exceptions as hdlc_exceptions


class HdlcParameterType(IntEnum):
    """
    HDLC Parameter Types as defined in DLMS Green Book Edition 9.
    
    These parameter IDs are used in SNRM/UA frame information fields
    for HDLC parameter negotiation according to Green Book section 8.4.5.3.2.

    Each parameter type has a specific format and valid range.
    """

    MAX_INFORMATION_FIELD_LENGTH_TX = 0x05
    """Maximum information field length for transmission (128-2048)."""

    MAX_INFORMATION_FIELD_LENGTH_RX = 0x06
    """Maximum information field length for reception (128-2048)."""

    WINDOW_SIZE_TX = 0x07
    """Window size for transmission (1-7)."""

    WINDOW_SIZE_RX = 0x08
    """Window size for reception (1-7)."""

    # Backward compatibility aliases (deprecated)
    WINDOW_SIZE = 0x07  # Alias for WINDOW_SIZE_TX
    MAX_INFORMATION_FIELD_LENGTH = 0x05  # Alias for MAX_INFORMATION_FIELD_LENGTH_TX


# Default values for HDLC parameters (when not negotiated)
DEFAULT_WINDOW_SIZE_TX = 1
DEFAULT_WINDOW_SIZE_RX = 1
DEFAULT_MAX_INFO_LENGTH = 128

# Backward compatibility alias (deprecated)
DEFAULT_WINDOW_SIZE = DEFAULT_WINDOW_SIZE_TX

# Format and group identifiers for SNRM/UA information field
FORMAT_IDENTIFIER = 0x81
GROUP_IDENTIFIER = 0x80


@attr.s(auto_attribs=True, frozen=True)
class HdlcParameterRange:
    """
    Valid range for an HDLC parameter.
    """

    min_value: int
    max_value: int
    default_value: int


# Parameter ranges based on DLMS/COSEM specification
PARAMETER_RANGES: Dict[HdlcParameterType, HdlcParameterRange] = {
    HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX: HdlcParameterRange(
        min_value=128, max_value=2048, default_value=DEFAULT_MAX_INFO_LENGTH
    ),
    HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX: HdlcParameterRange(
        min_value=128, max_value=2048, default_value=DEFAULT_MAX_INFO_LENGTH
    ),
    HdlcParameterType.WINDOW_SIZE_TX: HdlcParameterRange(
        min_value=1, max_value=7, default_value=DEFAULT_WINDOW_SIZE_TX
    ),
    HdlcParameterType.WINDOW_SIZE_RX: HdlcParameterRange(
        min_value=1, max_value=7, default_value=DEFAULT_WINDOW_SIZE_RX
    ),
    # Backward compatibility aliases
    HdlcParameterType.WINDOW_SIZE: HdlcParameterRange(
        min_value=1, max_value=7, default_value=DEFAULT_WINDOW_SIZE_TX
    ),
    HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH: HdlcParameterRange(
        min_value=128, max_value=2048, default_value=DEFAULT_MAX_INFO_LENGTH
    ),
}


@attr.s(auto_attribs=True)
class HdlcParameter:
    """
    A single HDLC parameter in TLV (Type-Length-Value) format.

    Attributes:
        param_type: Parameter type identifier
        value: Parameter value (integer)

    Example:
        >>> param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 3)
        >>> bytes(param)  # b'\\x01\\x01\\x03'
    """

    param_type: HdlcParameterType
    value: int

    # Parameter type to value length mapping
    # Note: Green Book allows 1 or 2 bytes for max info length (0x05/0x06)
    # and 1 or 4 bytes for window size (0x07/0x08)
    # We use minimal representation (1 byte for both)
    VALUE_LENGTHS: ClassVar[Dict[HdlcParameterType, int]] = {
        HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX: 1,  # Can be 1 or 2
        HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX: 1,  # Can be 1 or 2
        HdlcParameterType.WINDOW_SIZE_TX: 1,
        HdlcParameterType.WINDOW_SIZE_RX: 1,
        # Backward compatibility aliases
        HdlcParameterType.WINDOW_SIZE: 1,
        HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH: 1,
    }

    def validate(self) -> None:
        """
        Validate the parameter value against its allowed range.

        Raises:
            ValueError: If the value is out of range
        """
        if self.param_type not in PARAMETER_RANGES:
            raise ValueError(f"Unknown parameter type: {self.param_type}")

        range_info = PARAMETER_RANGES[self.param_type]
        if not (range_info.min_value <= self.value <= range_info.max_value):
            raise ValueError(
                f"{self.param_type.name} value {self.value} is out of range "
                f"[{range_info.min_value}, {range_info.max_value}]"
            )

    @property
    def length(self) -> int:
        """Return the length of the value field in bytes."""
        # Use minimal bytes needed
        if self.param_type in (
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX,
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX,
        ):
            # Use 1 byte for values <= 255, otherwise 2 bytes
            return 1 if self.value <= 255 else 2
        elif self.param_type in (
            HdlcParameterType.WINDOW_SIZE_TX,
            HdlcParameterType.WINDOW_SIZE_RX,
        ):
            # Window size is always 1 byte (1-7)
            return 1
        return self.VALUE_LENGTHS.get(self.param_type, 1)

    def to_bytes(self) -> bytes:
        """
        Encode the parameter to bytes in TLV format.

        Returns:
            TLV encoded parameter as bytes
        """
        self.validate()  # Validate before encoding

        type_byte = self.param_type.to_bytes(1, "big")
        length_byte = self.length.to_bytes(1, "big")

        # Encode value based on parameter type
        if self.param_type in (
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX,
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX,
        ):
            value_bytes = self.value.to_bytes(self.length, "big")
        elif self.param_type in (
            HdlcParameterType.WINDOW_SIZE_TX,
            HdlcParameterType.WINDOW_SIZE_RX,
        ):
            value_bytes = self.value.to_bytes(self.length, "big")
        else:
            # Fallback: try to encode with minimal bytes
            value_bytes = self.value.to_bytes(self.length, "big")

        return type_byte + length_byte + value_bytes

    @classmethod
    def from_bytes(cls, data: bytes, offset: int = 0) -> "HdlcParameter":
        """
        Decode a parameter from bytes at a given offset.

        Args:
            data: Byte array containing TLV encoded parameter
            offset: Starting position in the byte array

        Returns:
            HdlcParameter instance

        Raises:
            HdlcParsingError: If data is malformed
        """
        if len(data) < offset + 2:
            raise hdlc_exceptions.HdlcParsingError(
                f"Not enough data to decode parameter header. "
                f"Need at least 2 bytes, got {len(data) - offset}"
            )

        param_type = HdlcParameterType(data[offset])
        length = data[offset + 1]

        if len(data) < offset + 2 + length:
            raise hdlc_exceptions.HdlcParsingError(
                f"Not enough data for parameter value. "
                f"Expected {length} bytes, got {len(data) - offset - 2}"
            )

        # Decode value based on length
        value_bytes = data[offset + 2 : offset + 2 + length]
        value = int.from_bytes(value_bytes, "big")

        return cls(param_type, value)

    def __bytes__(self) -> bytes:
        """Return the byte representation of the parameter."""
        return self.to_bytes()


@attr.s(auto_attribs=True, repr=False)
class HdlcParameterList:
    """
    A list of HDLC parameters for negotiation during HDLC connection setup.

    This class manages a collection of parameters to be negotiated between
    client and server during HDLC connection establishment. Parameters are
    encoded using TLV (Type-Length-Value) format and transmitted in the
    information field of SNRM and UA frames.

    Supported Parameters:
        - Window size: Number of I-frames sent without acknowledgment (1-7)
        - Max info length TX: Maximum information field length for transmission (128-2048 bytes)
        - Max info length RX: Maximum information field length for reception (128-2048 bytes)

    Performance Impact:
        Larger window sizes and max info lengths can significantly improve
        throughput by reducing the overhead of acknowledgments and allowing
        more data to be transmitted per frame. However, both client and server
        must support the requested values.

    Examples:
        Basic usage:
        >>> params = HdlcParameterList()
        >>> params.set_window_size(3)
        >>> params.set_max_info_length_tx(512)
        >>> encoded = params.to_bytes()
        >>> b'\\x01\\x01\\x03' in encoded
        True

        Encoding and decoding:
        >>> params = HdlcParameterList()
        >>> params.set_window_size(5)
        >>> encoded = params.to_bytes()
        >>> decoded = HdlcParameterList.from_bytes(encoded)
        >>> decoded.window_size == 5
        True

        Getting negotiated values:
        >>> params = HdlcParameterList()
        >>> params.set_max_info_length_tx(1024)
        >>> params.set_max_info_length_rx(2048)
        >>> params.max_info_length  # Returns minimum of TX and RX
        1024

        Empty parameters (use defaults):
        >>> params = HdlcParameterList()
        >>> params.to_bytes()
        b''
    """

    _parameters: Dict[HdlcParameterType, HdlcParameter] = attr.ib(
        factory=dict, init=False
    )

    def set(self, param_type: HdlcParameterType, value: int) -> None:
        """
        Set a parameter value.

        Args:
            param_type: Parameter type
            value: Parameter value

        Raises:
            ValueError: If value is out of range
        """
        param = HdlcParameter(param_type, value)
        param.validate()
        self._parameters[param_type] = param

    def set_window_size_tx(self, window_size: int) -> None:
        """Set the window size for transmission (1-7)."""
        self.set(HdlcParameterType.WINDOW_SIZE_TX, window_size)

    def set_window_size_rx(self, window_size: int) -> None:
        """Set the window size for reception (1-7)."""
        self.set(HdlcParameterType.WINDOW_SIZE_RX, window_size)

    def set_max_info_length_tx(self, length: int) -> None:
        """Set the maximum information field length for transmission."""
        self.set(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, length)

    def set_max_info_length_rx(self, length: int) -> None:
        """Set the maximum information field length for reception."""
        self.set(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX, length)

    def get(self, param_type: HdlcParameterType, default: Optional[int] = None) -> Optional[int]:
        """
        Get a parameter value.

        Args:
            param_type: Parameter type to retrieve
            default: Default value if parameter not set

        Returns:
            Parameter value or default
        """
        if param_type in self._parameters:
            return self._parameters[param_type].value
        return default

    @property
    def window_size_tx(self) -> int:
        """Get the window size for transmission, or default if not set."""
        return self.get(HdlcParameterType.WINDOW_SIZE_TX, DEFAULT_WINDOW_SIZE_TX)

    @property
    def window_size_rx(self) -> int:
        """Get the window size for reception, or default if not set."""
        return self.get(HdlcParameterType.WINDOW_SIZE_RX, DEFAULT_WINDOW_SIZE_RX)

    @property
    def window_size(self) -> int:
        """
        Get the window size (backward compatibility).
        
        Returns window_size_tx for backward compatibility.
        Deprecated: Use window_size_tx or window_size_rx.
        """
        return self.window_size_tx

    @property
    def max_info_length_tx(self) -> int:
        """Get the max TX info length, or default if not set."""
        return self.get(
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, DEFAULT_MAX_INFO_LENGTH
        )

    @property
    def max_info_length_rx(self) -> int:
        """Get the max RX info length, or default if not set."""
        return self.get(
            HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX, DEFAULT_MAX_INFO_LENGTH
        )

    @property
    def max_info_length(self) -> int:
        """
        Get the maximum info length for both directions.

        Returns the minimum of TX and RX lengths if both are set,
        otherwise returns the one that is set, or default.
        """
        tx = self.get(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX)
        rx = self.get(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX)

        if tx is not None and rx is not None:
            return min(tx, rx)
        elif tx is not None:
            return tx
        elif rx is not None:
            return rx
        return DEFAULT_MAX_INFO_LENGTH

    def to_bytes(self, include_header: bool = True) -> bytes:
        """
        Encode all parameters to bytes with Green Book format.
        
        Green Book section 8.4.5.3.2 specifies:
        - Format identifier: 0x81
        - Group identifier: 0x80
        - Group length (1 byte): total length of all parameters
        - Parameters in TLV format

        Args:
            include_header: Whether to include 0x81/0x80/length header

        Returns:
            Encoded parameters
        """
        if not self._parameters:
            return b""

        # Encode parameters in order of type (for consistency)
        params_bytes = b""
        for param_type in sorted(self._parameters.keys()):
            params_bytes += self._parameters[param_type].to_bytes()

        if not include_header:
            return params_bytes

        # Add Green Book header: 0x81, 0x80, group_length
        header = bytes([
            FORMAT_IDENTIFIER,
            GROUP_IDENTIFIER,
            len(params_bytes)
        ])
        
        return header + params_bytes

    @classmethod
    def from_bytes(cls, data: bytes, has_header: bool = True) -> "HdlcParameterList":
        """
        Decode parameters from bytes.
        
        Green Book format includes header:
        - 0x81 format identifier
        - 0x80 group identifier
        - group length (1 byte)
        - parameters in TLV format

        Args:
            data: Byte array containing TLV encoded parameters
            has_header: Whether data includes 0x81/0x80/length header

        Returns:
            HdlcParameterList instance

        Raises:
            HdlcParsingError: If data is malformed
        """
        params = cls()
        offset = 0

        # Skip Green Book header if present
        if has_header and len(data) >= 3:
            if data[0] == FORMAT_IDENTIFIER and data[1] == GROUP_IDENTIFIER:
                group_length = data[2]
                offset = 3
                # Verify length matches
                if len(data) < 3 + group_length:
                    raise hdlc_exceptions.HdlcParsingError(
                        f"Data too short for group length {group_length}, "
                        f"got {len(data) - 3} bytes"
                    )

        while offset < len(data):
            param = HdlcParameter.from_bytes(data, offset)
            params._parameters[param.param_type] = param

            # Move to next parameter
            offset += 2 + param.length  # type (1) + length (1) + value

        return params

    def merge(self, other: "HdlcParameterList") -> "HdlcParameterList":
        """
        Merge another parameter list into this one.

        Values from the other list take precedence.

        Args:
            other: Another HdlcParameterList

        Returns:
            A new HdlcParameterList with merged parameters
        """
        result = HdlcParameterList()
        result._parameters = {**self._parameters, **other._parameters}
        return result

    def __bytes__(self) -> bytes:
        """Return the byte representation of all parameters."""
        return self.to_bytes()

    def __len__(self) -> int:
        """Return the number of parameters in the list."""
        return len(self._parameters)

    def __contains__(self, param_type: HdlcParameterType) -> bool:
        """Check if a parameter type is in the list."""
        return param_type in self._parameters

    def __repr__(self) -> str:
        """String representation showing all parameters."""
        items = []
        for param_type in sorted(self._parameters.keys(), key=lambda x: x.value):
            param = self._parameters[param_type]
            items.append(f"{param_type.name}={param.value}")
        return f"HdlcParameterList({', '.join(items)})"


def negotiate_parameters(
    client_params: HdlcParameterList, server_params: HdlcParameterList
) -> HdlcParameterList:
    """
    Negotiate HDLC parameters between client and server.

    During HDLC connection setup, both client and server propose their
    maximum capabilities. The final negotiated value for each parameter
    is the minimum of the two proposals, ensuring both sides can handle
    the communication.
    
    Note: Client's TX parameters correspond to server's RX and vice versa.
    For example, client's MAX_INFO_FIELD_LENGTH_TX matches against
    server's MAX_INFO_FIELD_LENGTH_RX.

    Negotiation Rules:
        - If client doesn't set a parameter, default value is used
        - If server doesn't set a parameter, default value is used
        - Final value = min(client_value, server_value, max_allowed_value)

    Args:
        client_params: Parameters proposed by the client
        server_params: Parameters proposed by the server

    Returns:
        A new HdlcParameterList containing negotiated values

    Examples:
        Basic negotiation:
        >>> client = HdlcParameterList()
        >>> client.set_window_size_tx(5)
        >>> client.set_max_info_length_tx(1024)
        >>> server = HdlcParameterList()
        >>> server.set_window_size_rx(3)
        >>> server.set_max_info_length_rx(512)
        >>> negotiated = negotiate_parameters(client, server)
        >>> negotiated.window_size_tx
        3
        >>> negotiated.max_info_length_tx
        512
    """
    negotiated = HdlcParameterList()

    # Map client TX parameters to server RX parameters and vice versa
    param_pairs = [
        (HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 
         HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_RX),
        (HdlcParameterType.WINDOW_SIZE_TX, 
         HdlcParameterType.WINDOW_SIZE_RX),
    ]

    for client_type, server_type in param_pairs:
        # Get default range
        if client_type not in PARAMETER_RANGES:
            continue

        range_info = PARAMETER_RANGES[client_type]

        client_value = client_params.get(client_type, range_info.default_value)
        # Match client TX with server RX
        server_value = server_params.get(server_type, range_info.default_value)

        # Negotiate: use minimum (both represent maximum capabilities)
        negotiated_value = min(client_value, server_value)

        # Ensure the negotiated value is within valid range
        negotiated_value = max(
            range_info.min_value, min(negotiated_value, range_info.max_value)
        )

        negotiated._parameters[client_type] = HdlcParameter(client_type, negotiated_value)

    # Also negotiate the reverse direction (client RX with server TX)
    for server_type, client_type in param_pairs:
        if server_type not in PARAMETER_RANGES:
            continue

        range_info = PARAMETER_RANGES[server_type]

        server_value = server_params.get(server_type, range_info.default_value)
        client_value = client_params.get(client_type, range_info.default_value)

        negotiated_value = min(client_value, server_value)
        negotiated_value = max(
            range_info.min_value, min(negotiated_value, range_info.max_value)
        )

        if server_type not in negotiated._parameters:
            negotiated._parameters[server_type] = HdlcParameter(server_type, negotiated_value)

    return negotiated
