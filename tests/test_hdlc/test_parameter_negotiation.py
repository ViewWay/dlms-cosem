"""
Tests for HDLC parameter negotiation.
"""
import pytest

from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.hdlc.exceptions import HdlcParsingError
from dlms_cosem.hdlc.frames import (
    SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame,
)
from dlms_cosem.hdlc.parameters import (
    DEFAULT_MAX_INFO_LENGTH,
    DEFAULT_WINDOW_SIZE,
    HdlcParameter,
    HdlcParameterList,
    HdlcParameterType,
    negotiate_parameters,
)


class TestHdlcParameter:
    """Tests for individual HDLC parameters."""

    def test_create_window_size_parameter(self):
        """Test creating a window size parameter."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 3)
        assert param.param_type == HdlcParameterType.WINDOW_SIZE
        assert param.value == 3
        assert param.length == 1

    def test_create_max_info_length_parameter(self):
        """Test creating a max info length parameter."""
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 512)
        assert param.param_type == HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX
        assert param.value == 512
        assert param.length == 2

    def test_window_size_validation_passes(self):
        """Test that valid window size passes validation."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 5)
        param.validate()  # Should not raise

    def test_window_size_validation_fails_low(self):
        """Test that window size below minimum fails validation."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 0)
        with pytest.raises(ValueError, match="out of range"):
            param.validate()

    def test_window_size_validation_fails_high(self):
        """Test that window size above maximum fails validation."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 10)
        with pytest.raises(ValueError, match="out of range"):
            param.validate()

    def test_max_info_length_validation_passes(self):
        """Test that valid max info length passes validation."""
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 1024)
        param.validate()  # Should not raise

    def test_max_info_length_validation_fails_low(self):
        """Test that max info length below minimum fails validation."""
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 64)
        with pytest.raises(ValueError, match="out of range"):
            param.validate()

    def test_max_info_length_validation_fails_high(self):
        """Test that max info length above maximum fails validation."""
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 3000)
        with pytest.raises(ValueError, match="out of range"):
            param.validate()

    def test_encode_window_size_parameter(self):
        """Test encoding a window size parameter."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 3)
        encoded = param.to_bytes()
        assert encoded == b"\x01\x01\x03"  # type=1, length=1, value=3

    def test_encode_max_info_length_parameter(self):
        """Test encoding a max info length parameter."""
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 512)
        encoded = param.to_bytes()
        assert encoded == b"\x02\x02\x02\x00"  # type=2, length=2, value=512

    def test_decode_window_size_parameter(self):
        """Test decoding a window size parameter."""
        data = b"\x01\x01\x03"
        param = HdlcParameter.from_bytes(data)
        assert param.param_type == HdlcParameterType.WINDOW_SIZE
        assert param.value == 3

    def test_decode_max_info_length_parameter(self):
        """Test decoding a max info length parameter."""
        data = b"\x02\x02\x02\x00"
        param = HdlcParameter.from_bytes(data)
        assert param.param_type == HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX
        assert param.value == 512

    def test_decode_with_offset(self):
        """Test decoding a parameter with an offset."""
        data = b"\xff\x01\x01\x05"
        param = HdlcParameter.from_bytes(data, offset=1)
        assert param.param_type == HdlcParameterType.WINDOW_SIZE
        assert param.value == 5

    def test_decode_fails_with_insufficient_data(self):
        """Test that decoding fails with insufficient data."""
        data = b"\x01"  # Only type byte
        with pytest.raises(HdlcParsingError, match="Not enough data"):
            HdlcParameter.from_bytes(data)

    def test_decode_fails_with_insufficient_value_data(self):
        """Test that decoding fails when value data is incomplete."""
        data = b"\x02\x02\x00"  # type=2, length=2, but only 1 byte of value
        with pytest.raises(HdlcParsingError, match="Not enough data for parameter value"):
            HdlcParameter.from_bytes(data)

    def test_bytes_magic_method(self):
        """Test the __bytes__ magic method."""
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE, 3)
        assert bytes(param) == b"\x01\x01\x03"


class TestHdlcParameterList:
    """Tests for HDLC parameter lists."""

    def test_create_empty_list(self):
        """Test creating an empty parameter list."""
        params = HdlcParameterList()
        assert len(params) == 0
        assert params.to_bytes() == b""

    def test_set_window_size(self):
        """Test setting window size."""
        params = HdlcParameterList()
        params.set_window_size(3)
        assert params.window_size == 3

    def test_set_max_info_length(self):
        """Test setting max info length."""
        params = HdlcParameterList()
        params.set_max_info_length_tx(512)
        assert params.max_info_length_tx == 512

    def test_set_max_info_length_rx(self):
        """Test setting max info length RX."""
        params = HdlcParameterList()
        params.set_max_info_length_rx(1024)
        assert params.max_info_length_rx == 1024

    def test_max_info_length_returns_minimum(self):
        """Test that max_info_length returns minimum of TX and RX."""
        params = HdlcParameterList()
        params.set_max_info_length_tx(512)
        params.set_max_info_length_rx(1024)
        assert params.max_info_length == 512

    def test_max_info_length_returns_tx_if_rx_not_set(self):
        """Test that max_info_length returns TX if RX is not set."""
        params = HdlcParameterList()
        params.set_max_info_length_tx(512)
        assert params.max_info_length == 512

    def test_default_window_size(self):
        """Test default window size when not set."""
        params = HdlcParameterList()
        assert params.window_size == DEFAULT_WINDOW_SIZE

    def test_default_max_info_length(self):
        """Test default max info length when not set."""
        params = HdlcParameterList()
        assert params.max_info_length == DEFAULT_MAX_INFO_LENGTH

    def test_get_returns_value_when_set(self):
        """Test that get returns value when parameter is set."""
        params = HdlcParameterList()
        params.set(HdlcParameterType.WINDOW_SIZE, 5)
        assert params.get(HdlcParameterType.WINDOW_SIZE) == 5

    def test_get_returns_default_when_not_set(self):
        """Test that get returns default when parameter is not set."""
        params = HdlcParameterList()
        assert params.get(HdlcParameterType.WINDOW_SIZE, 99) == 99

    def test_get_returns_none_when_not_set_and_no_default(self):
        """Test that get returns None when parameter is not set and no default."""
        params = HdlcParameterList()
        assert params.get(HdlcParameterType.WINDOW_SIZE) is None

    def test_encode_single_parameter(self):
        """Test encoding a single parameter."""
        params = HdlcParameterList()
        params.set_window_size(3)
        encoded = params.to_bytes()
        assert encoded == b"\x01\x01\x03"

    def test_encode_multiple_parameters(self):
        """Test encoding multiple parameters."""
        params = HdlcParameterList()
        params.set_window_size(3)
        params.set_max_info_length_tx(512)
        encoded = params.to_bytes()
        # Parameters are encoded in type order
        assert encoded == b"\x01\x01\x03\x02\x02\x02\x00"

    def test_decode_empty_list(self):
        """Test decoding an empty parameter list."""
        params = HdlcParameterList.from_bytes(b"")
        assert len(params) == 0

    def test_decode_single_parameter(self):
        """Test decoding a single parameter."""
        data = b"\x01\x01\x03"
        params = HdlcParameterList.from_bytes(data)
        assert len(params) == 1
        assert params.window_size == 3

    def test_decode_multiple_parameters(self):
        """Test decoding multiple parameters."""
        data = b"\x01\x01\x03\x02\x02\x02\x00"
        params = HdlcParameterList.from_bytes(data)
        assert len(params) == 2
        assert params.window_size == 3
        assert params.max_info_length_tx == 512

    def test_contains_operator(self):
        """Test the 'in' operator."""
        params = HdlcParameterList()
        params.set_window_size(3)
        assert HdlcParameterType.WINDOW_SIZE in params
        assert HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX not in params

    def test_repr(self):
        """Test string representation."""
        params = HdlcParameterList()
        params.set_window_size(3)
        params.set_max_info_length_tx(512)
        repr_str = repr(params)
        assert "WINDOW_SIZE=3" in repr_str
        assert "MAX_INFORMATION_FIELD_LENGTH_TX=512" in repr_str

    def test_set_validates_parameter(self):
        """Test that set validates the parameter."""
        params = HdlcParameterList()
        with pytest.raises(ValueError, match="out of range"):
            params.set_window_size(10)

    def test_merge_two_lists(self):
        """Test merging two parameter lists."""
        params1 = HdlcParameterList()
        params1.set_window_size(3)
        params2 = HdlcParameterList()
        params2.set_max_info_length_tx(512)
        merged = params1.merge(params2)
        assert merged.window_size == 3
        assert merged.max_info_length_tx == 512

    def test_merge_overwrites_values(self):
        """Test that merge overwrites existing values."""
        params1 = HdlcParameterList()
        params1.set_window_size(3)
        params2 = HdlcParameterList()
        params2.set_window_size(5)
        merged = params1.merge(params2)
        assert merged.window_size == 5


class TestNegotiateParameters:
    """Tests for parameter negotiation."""

    def test_negotiate_window_size_minimum(self):
        """Test that negotiation uses minimum value."""
        client = HdlcParameterList()
        client.set_window_size(5)
        server = HdlcParameterList()
        server.set_window_size(3)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == 3

    def test_negotiate_max_info_length_minimum(self):
        """Test that negotiation uses minimum value."""
        client = HdlcParameterList()
        client.set_max_info_length_tx(1024)
        server = HdlcParameterList()
        server.set_max_info_length_tx(512)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.max_info_length_tx == 512

    def test_negotiate_uses_default_when_client_not_set(self):
        """Test that negotiation uses default when client doesn't set parameter."""
        client = HdlcParameterList()
        server = HdlcParameterList()
        server.set_window_size(3)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == DEFAULT_WINDOW_SIZE

    def test_negotiate_uses_default_when_server_not_set(self):
        """Test that negotiation uses default when server doesn't set parameter."""
        client = HdlcParameterList()
        client.set_window_size(5)
        server = HdlcParameterList()
        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == DEFAULT_WINDOW_SIZE

    def test_negotiate_all_parameters(self):
        """Test negotiating all parameters together."""
        client = HdlcParameterList()
        client.set_window_size(5)
        client.set_max_info_length_tx(1024)
        client.set_max_info_length_rx(2048)

        server = HdlcParameterList()
        server.set_window_size(3)
        server.set_max_info_length_tx(512)
        server.set_max_info_length_rx(1024)

        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == 3
        assert negotiated.max_info_length_tx == 512
        assert negotiated.max_info_length_rx == 1024


class TestSetNormalResponseModeFrame:
    """Tests for SNRM frame with parameter negotiation."""

    def test_snrm_without_parameters(self):
        """Test SNRM frame without parameters."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        frame = SetNormalResponseModeFrame(client_addr, server_addr)

        # Should have no information field
        assert frame.information == b""
        assert frame.parameters.to_bytes() == b""

    def test_snrm_with_parameters(self):
        """Test SNRM frame with parameters."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)
        params.set_max_info_length_tx(512)

        frame = SetNormalResponseModeFrame(client_addr, server_addr, parameters=params)

        # Information field should contain encoded parameters
        assert frame.information == b"\x01\x01\x03\x02\x02\x02\x00"

    def test_snrm_frame_length_with_parameters(self):
        """Test that frame length is calculated correctly with parameters."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)

        frame = SetNormalResponseModeFrame(client_addr, server_addr, parameters=params)

        # Frame length should include parameters (and HCS)
        expected_length = (
            5  # fixed_length_bytes
            + 1  # client address length
            + 1  # server address length
            + 3  # parameters (type + length + value)
            + 2  # HCS (present when parameters are present)
        )
        assert frame.frame_length == expected_length

    def test_snrm_hcs_with_parameters(self):
        """Test that HCS is calculated when parameters are present."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)

        frame = SetNormalResponseModeFrame(client_addr, server_addr, parameters=params)

        # HCS should be present
        assert len(frame.hcs) == 2

    def test_snrm_hcs_without_parameters(self):
        """Test that HCS is not present when parameters are absent."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        frame = SetNormalResponseModeFrame(client_addr, server_addr)

        # HCS should not be present
        assert frame.hcs == b""


class TestUnNumberedAcknowledgmentFrame:
    """Tests for UA frame with parameter negotiation."""

    def test_ua_without_parameters(self):
        """Test UA frame without parameters."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        frame = UnNumberedAcknowledgmentFrame(client_addr, server_addr)

        assert frame.information == b""
        assert len(frame.parameters) == 0

    def test_ua_with_parameters(self):
        """Test UA frame with parameters."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)

        frame = UnNumberedAcknowledgmentFrame(
            client_addr, server_addr, parameters=params
        )

        assert frame.information == b"\x01\x01\x03"
        assert frame.parameters.window_size == 3

    def test_ua_with_payload_for_backward_compatibility(self):
        """Test UA frame with raw payload (backward compatibility)."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        frame = UnNumberedAcknowledgmentFrame(
            client_addr, server_addr, payload=b"\xff\xff"
        )

        assert frame.information == b"\xff\xff"

    def test_ua_with_both_parameters_and_payload(self):
        """Test UA frame with both parameters and payload."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)

        frame = UnNumberedAcknowledgmentFrame(
            client_addr, server_addr, payload=b"\xff\xff", parameters=params
        )

        # Both should be in the information field
        assert frame.information == b"\x01\x01\x03\xff\xff"

    def test_ua_from_bytes_with_parameters(self):
        """Test parsing UA frame with parameters from bytes."""
        # Construct a UA frame with parameters
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")

        params = HdlcParameterList()
        params.set_window_size(3)

        original_frame = UnNumberedAcknowledgmentFrame(
            client_addr, server_addr, parameters=params
        )

        frame_bytes = original_frame.to_bytes()

        # Parse the frame
        parsed_frame = UnNumberedAcknowledgmentFrame.from_bytes(frame_bytes)

        # Check that parameters were parsed
        assert parsed_frame.parameters.window_size == 3

    def test_ua_from_bytes_without_parameters(self):
        """Test parsing UA frame without parameters from bytes."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        original_frame = UnNumberedAcknowledgmentFrame(client_addr, server_addr)

        frame_bytes = original_frame.to_bytes()
        parsed_frame = UnNumberedAcknowledgmentFrame.from_bytes(frame_bytes)

        assert len(parsed_frame.parameters) == 0

    def test_ua_from_bytes_with_payload(self):
        """Test parsing UA frame with raw payload from bytes."""
        client_addr = HdlcAddress(0x01, None, "client")
        server_addr = HdlcAddress(0x01, None, "server")
        original_frame = UnNumberedAcknowledgmentFrame(
            client_addr, server_addr, payload=b"\xff\xff"
        )

        frame_bytes = original_frame.to_bytes()
        parsed_frame = UnNumberedAcknowledgmentFrame.from_bytes(frame_bytes)

        # Payload should be preserved
        assert parsed_frame.payload == b"\xff\xff"
