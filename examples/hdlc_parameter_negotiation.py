#!/usr/bin/env python3
"""
HDLC Parameter Negotiation Example

This example demonstrates how to use HDLC parameter negotiation
to optimize communication parameters when establishing a connection
with a DLMS/COSEM meter.

HDLC parameters that can be negotiated:
- Window size: Number of I-frames that can be sent without acknowledgment (1-7)
- Max info length TX: Maximum information field length for transmission (128-2048 bytes)
- Max info length RX: Maximum information field length for reception (128-2048 bytes)

Larger values can improve performance but require both client and meter support.
"""
from dlms_cosem.hdlc import (
    HdlcAddress,
    HdlcParameterList,
    HdlcParameterType,
    SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame,
    negotiate_parameters,
)


def example_basic_parameter_negotiation():
    """
    Example 1: Basic parameter negotiation.

    Client proposes window size of 5 and max info length of 1024 bytes.
    Server responds with its capabilities.
    """
    print("=== Example 1: Basic Parameter Negotiation ===\n")

    # Client creates SNRM frame with proposed parameters
    client_params = HdlcParameterList()
    client_params.set_window_size(5)  # Can send up to 5 frames without waiting for ACK
    client_params.set_max_info_length_tx(1024)  # Can send up to 1024 bytes
    client_params.set_max_info_length_rx(2048)  # Can receive up to 2048 bytes

    print(f"Client proposes: {client_params}")

    # Create SNRM frame
    client_addr = HdlcAddress(0x01, None, "client")
    server_addr = HdlcAddress(0x01, None, "server")

    snrm_frame = SetNormalResponseModeFrame(
        destination_address=client_addr,
        source_address=server_addr,
        parameters=client_params,
    )

    print(f"SNRM frame info field: {snrm_frame.information.hex()}")
    print()

    # Simulate server response (meter responds with its own capabilities)
    server_params = HdlcParameterList()
    server_params.set_window_size(3)  # Meter only supports window size of 3
    server_params.set_max_info_length_tx(512)  # Meter max TX is 512 bytes
    server_params.set_max_info_length_rx(1024)  # Meter max RX is 1024 bytes

    print(f"Server responds: {server_params}")

    # Negotiate final parameters (use minimum of client and server values)
    negotiated = negotiate_parameters(client_params, server_params)

    print(f"Negotiated parameters: {negotiated}")
    print(f"  Window size: {negotiated.window_size}")
    print(f"  Max TX length: {negotiated.max_info_length_tx}")
    print(f"  Max RX length: {negotiated.max_info_length_rx}")
    print()


def example_default_parameters():
    """
    Example 2: Using default parameters (no negotiation).

    If no parameters are negotiated, default values will be used:
    - Window size = 1
    - Max info length = 128 bytes
    """
    print("=== Example 2: Default Parameters (No Negotiation) ===\n")

    # Create SNRM without parameters
    client_addr = HdlcAddress(0x01, None, "client")
    server_addr = HdlcAddress(0x01, None, "server")

    snrm_frame = SetNormalResponseModeFrame(
        destination_address=client_addr,
        source_address=server_addr,
    )

    print("SNRM without parameters (uses defaults)")
    print(f"  Information field: {snrm_frame.information}")
    print(f"  Length: {len(snrm_frame.information)} bytes")
    print()

    # Default values
    from dlms_cosem.hdlc.parameters import (
        DEFAULT_MAX_INFO_LENGTH,
        DEFAULT_WINDOW_SIZE,
    )

    print(f"Default values will be used:")
    print(f"  Window size: {DEFAULT_WINDOW_SIZE}")
    print(f"  Max info length: {DEFAULT_MAX_INFO_LENGTH}")
    print()


def example_ua_frame_with_parameters():
    """
    Example 3: UA frame with negotiated parameters.

    The server (meter) responds with a UA frame containing the
    negotiated parameters.
    """
    print("=== Example 3: UA Frame with Negotiated Parameters ===\n")

    # Server creates UA frame with negotiated parameters
    client_addr = HdlcAddress(0x01, None, "client")
    server_addr = HdlcAddress(0x01, None, "server")

    negotiated_params = HdlcParameterList()
    negotiated_params.set_window_size(3)
    negotiated_params.set_max_info_length_tx(512)

    ua_frame = UnNumberedAcknowledgmentFrame(
        destination_address=server_addr,
        source_address=client_addr,
        parameters=negotiated_params,
    )

    print(f"UA frame with negotiated parameters: {negotiated_params}")
    print(f"UA frame info field: {ua_frame.information.hex()}")
    print()


def example_parameter_validation():
    """
    Example 4: Parameter validation.

    Parameters are validated to ensure they are within allowed ranges.
    """
    print("=== Example 4: Parameter Validation ===\n")

    try:
        # Try to set window size outside valid range (1-7)
        params = HdlcParameterList()
        params.set_window_size(10)  # Invalid!
    except ValueError as e:
        print(f"Validation error: {e}")

    try:
        # Try to set max info length outside valid range (128-2048)
        params = HdlcParameterList()
        params.set_max_info_length_tx(100)  # Too small!
    except ValueError as e:
        print(f"Validation error: {e}")

    print("\nValid parameter ranges:")
    print("  Window size: 1-7")
    print("  Max info length: 128-2048 bytes")
    print()


def example_encoding_decoding():
    """
    Example 5: Encoding and decoding parameters.

    Demonstrates the TLV (Type-Length-Value) encoding used for
    HDLC parameters.
    """
    print("=== Example 5: Parameter Encoding/Decoding ===\n")

    # Create parameters
    params = HdlcParameterList()
    params.set_window_size(3)
    params.set_max_info_length_tx(512)

    # Encode to bytes (TLV format)
    encoded = params.to_bytes()
    print(f"Encoded parameters: {encoded.hex()}")
    print(f"  Type (0x01): window size")
    print(f"  Length (0x01): 1 byte")
    print(f"  Value (0x03): 3")
    print(f"  Type (0x02): max info length TX")
    print(f"  Length (0x02): 2 bytes")
    print(f"  Value (0x0200): 512")
    print()

    # Decode from bytes
    decoded = HdlcParameterList.from_bytes(encoded)
    print(f"Decoded parameters: {decoded}")
    print(f"  Window size: {decoded.window_size}")
    print(f"  Max TX length: {decoded.max_info_length_tx}")
    print()


def example_performance_comparison():
    """
    Example 6: Performance comparison of different parameter settings.

    Shows how different parameter settings affect theoretical throughput.
    """
    print("=== Example 6: Performance Comparison ===\n")

    scenarios = [
        ("Default (no negotiation)", 1, 128),
        ("Conservative", 2, 256),
        ("Moderate", 3, 512),
        ("Aggressive", 5, 1024),
    ]

    print("Scenario                    Window  MaxLen  Throughput (bytes/round-trip)")
    print("────────────────────────────────────────────────────────────────────────")

    for name, window, max_len in scenarios:
        # Rough throughput calculation: window * max_len
        throughput = window * max_len
        print(f"{name:26} {window:7} {max_len:7} {throughput:20}")

    print()
    print("Note: Actual throughput depends on network latency and meter capabilities.")
    print()


if __name__ == "__main__":
    example_basic_parameter_negotiation()
    example_default_parameters()
    example_ua_frame_with_parameters()
    example_parameter_validation()
    example_encoding_decoding()
    example_performance_comparison()

    print("\n=== Key Takeaways ===")
    print("1. HDLC parameter negotiation can significantly improve performance")
    print("2. Both client and server must support the requested parameters")
    print("3. Negotiated values are the minimum of client and server proposals")
    print("4. Always validate parameters are within allowed ranges")
    print("5. Default values provide broad compatibility but lower performance")
