"""Enhanced parameter negotiation boundary and edge case tests."""

import pytest

from dlms_cosem.hdlc.parameters import (
    HdlcParameter,
    HdlcParameterList,
    HdlcParameterType,
    negotiate_parameters,
)


class TestBoundaryValues:
    """Window size and max info length boundary tests."""

    def test_window_size_minimum_valid(self):
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE_TX, 1)
        param.validate()  # Should not raise

    def test_window_size_maximum_valid(self):
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE_TX, 7)
        param.validate()  # max valid is 7 for this implementation

    def test_window_size_zero_invalid(self):
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE_TX, 0)
        with pytest.raises(ValueError):
            param.validate()

    def test_window_size_overflow_invalid(self):
        param = HdlcParameter(HdlcParameterType.WINDOW_SIZE_TX, 8)
        with pytest.raises(ValueError):
            param.validate()

    def test_max_info_length_minimum_valid(self):
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 128)
        param.validate()

    def test_max_info_length_boundary_values(self):
        """Test common max info length boundaries."""
        for val in [128, 256, 512, 1024, 2048]:
            param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, val)
            param.validate()  # Should not raise

    def test_max_info_length_too_large(self):
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 65536)
        with pytest.raises(ValueError):
            param.validate()

    def test_max_info_length_zero_invalid(self):
        param = HdlcParameter(HdlcParameterType.MAX_INFORMATION_FIELD_LENGTH_TX, 0)
        with pytest.raises(ValueError):
            param.validate()


class TestNegotiationBoundary:
    """Parameter negotiation boundary cases."""

    def test_negotiate_both_empty_uses_defaults(self):
        client = HdlcParameterList()
        server = HdlcParameterList()
        negotiated = negotiate_parameters(client, server)
        # Should use defaults without error
        assert negotiated.window_size > 0
        assert negotiated.max_info_length > 0

    def test_negotiate_window_size_one(self):
        client = HdlcParameterList()
        client.set_window_size_tx(1)
        client.set_window_size_rx(1)
        server = HdlcParameterList()
        server.set_window_size_tx(1)
        server.set_window_size_rx(1)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == 1

    def test_negotiate_max_info_asymmetric(self):
        client = HdlcParameterList()
        client.set_max_info_length_tx(2048)
        client.set_max_info_length_rx(2048)
        server = HdlcParameterList()
        server.set_max_info_length_tx(128)
        server.set_max_info_length_rx(128)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.max_info_length_tx == 128

    def test_merge_preserves_all_parameters(self):
        p1 = HdlcParameterList()
        p1.set_window_size_tx(5)
        p1.set_window_size_rx(5)
        p2 = HdlcParameterList()
        p2.set_max_info_length_tx(512)
        p2.set_max_info_length_rx(1024)
        merged = p1.merge(p2)
        assert merged.window_size == 5
        assert merged.max_info_length_tx == 512
        assert merged.max_info_length_rx == 1024


class TestInvalidParameterRejection:
    """Test that invalid parameters are rejected."""

    def test_set_invalid_window_size_rejected(self):
        params = HdlcParameterList()
        with pytest.raises(ValueError):
            params.set_window_size_tx(0)
        with pytest.raises(ValueError):
            params.set_window_size_rx(0)

    def test_set_invalid_max_info_length_rejected(self):
        params = HdlcParameterList()
        with pytest.raises(ValueError):
            params.set_max_info_length_tx(0)
        with pytest.raises(ValueError):
            params.set_max_info_length_rx(0)
