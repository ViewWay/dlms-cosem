"""Tests for protocol frame modules (gateway, RF)."""
import pytest

from dlms_cosem.protocol.frame.gateway import GatewayFrame, GatewayResponseFrame
from dlms_cosem.protocol.frame.rf import RFFrame, RFSignalQuality, RFChannelState, crc16_ccitt


class TestRFSignalQuality:
    """Test RF signal quality metrics."""

    def test_default_values(self):
        sq = RFSignalQuality()
        assert sq.uplink_signal_strength == 0
        assert sq.uplink_snr == 0
        assert sq.downlink_signal_strength == 0
        assert sq.downlink_snr == 0

    def test_from_bytes(self):
        data = bytes.fromhex("001A 002B 003C 004D")
        sq = RFSignalQuality.from_bytes(data)
        assert sq.uplink_signal_strength == 0x001A
        assert sq.uplink_snr == 0x002B
        assert sq.downlink_signal_strength == 0x003C
        assert sq.downlink_snr == 0x004D

    def test_to_bytes(self):
        sq = RFSignalQuality(
            uplink_signal_strength=0x001A,
            uplink_snr=0x002B,
            downlink_signal_strength=0x003C,
            downlink_snr=0x004D,
        )
        data = sq.to_bytes()
        assert data == bytes.fromhex("001A 002B 003C 004D")

    def test_roundtrip(self):
        original = RFSignalQuality(100, 200, 150, 180)
        data = original.to_bytes()
        restored = RFSignalQuality.from_bytes(data)
        assert restored.uplink_signal_strength == 100
        assert restored.uplink_snr == 200
        assert restored.downlink_signal_strength == 150
        assert restored.downlink_snr == 180

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            RFSignalQuality.from_bytes(b"\x00\x01")


class TestRFChannelState:
    """Test RF channel state information."""

    def test_default_values(self):
        cs = RFChannelState()
        assert cs.link_state == 0
        assert cs.channel_state == 0

    def test_from_bytes(self):
        data = bytes.fromhex("1234 5678")
        cs = RFChannelState.from_bytes(data)
        assert cs.link_state == 0x1234
        assert cs.channel_state == 0x5678

    def test_to_bytes(self):
        cs = RFChannelState(link_state=0x1234, channel_state=0x5678)
        data = cs.to_bytes()
        assert data == bytes.fromhex("1234 5678")

    def test_roundtrip(self):
        original = RFChannelState(0xABCD, 0xEF01)
        data = original.to_bytes()
        restored = RFChannelState.from_bytes(data)
        assert restored.link_state == 0xABCD
        assert restored.channel_state == 0xEF01


class TestCRC16:
    """Test CRC-16/CCITT calculation."""

    def test_crc16_known_values(self):
        # Test known CRC values
        assert crc16_ccitt(b"\x00") == bytes.fromhex("0000")
        assert crc16_ccitt(b"\xFF\xFF") == bytes.fromhex("F0F8")

    def test_crc16_consistency(self):
        data = b"Test data for CRC"
        crc1 = crc16_ccitt(data)
        crc2 = crc16_ccitt(data)
        assert crc1 == crc2


class TestRFFrame:
    """Test RF Frame encoding/decoding."""

    def test_default_frame(self):
        frame = RFFrame()
        assert frame.dcu_address == b'\x00' * 8
        assert frame.meter_address == b'\x00' * 16
        assert frame.communication_type == 0x21
        assert frame.frame_sequence == 0x01

    def test_communication_types(self):
        assert RFFrame.COMM_TYPE_READ == 0x21
        assert RFFrame.COMM_TYPE_COMMAND == 0x22

    def test_to_bytes_basic(self):
        frame = RFFrame(
            dcu_address=b'\x01\x02\x03\x04\x05\x06\x07\x08',
            meter_address=b'\x00' * 16,
            communication_type=0x21,
            frame_sequence=1,
            data_apdu=b'\x5A',
        )
        data = frame.to_bytes()
        assert data[0] == 0x68  # Start bit
        assert data[-1] == 0x16  # End bit

    def test_scan_channel(self):
        frame = RFFrame()
        scan_data = frame.scan_channel(channel=1)
        assert len(scan_data) > 0
        assert scan_data[0] == 0x68  # Start bit
        assert scan_data[-1] == 0x16  # End bit

    def test_scan_invalid_channel(self):
        frame = RFFrame()
        with pytest.raises(ValueError):
            frame.scan_channel(channel=10)

    def test_connect_meter(self):
        frame = RFFrame()
        connect_data = frame.connect_meter(channel=2)
        assert len(connect_data) > 0
        assert connect_data[0] == 0x68

    def test_negotiate_parameters(self):
        frame = RFFrame()
        negotiate_data = frame.negotiate_parameters(channel=3)
        assert len(negotiate_data) > 0
        assert negotiate_data[0] == 0x68

    def test_invalid_start_bit(self):
        # Create invalid frame data
        invalid_data = b'\x00' + b'\x00' * 40
        with pytest.raises(ValueError, match="Invalid RF Frame start bit"):
            RFFrame.from_bytes(invalid_data)

    def test_too_short_frame(self):
        with pytest.raises(ValueError, match="at least 40 bytes"):
            RFFrame.from_bytes(b'\x68' + b'\x00' * 10)


class TestGatewayFrame:
    """Test Gateway Frame encoding/decoding."""

    def test_default_frame(self):
        gw = GatewayFrame()
        assert gw.network_id == 0x00
        assert gw.physical_address == ""
        assert gw.user_info == b""
        assert gw.src_wport == 16
        assert gw.dst_wport == 1

    def test_gateway_header(self):
        assert GatewayFrame.GATEWAY_HEADER == 0xE6

    def test_to_bytes_basic(self):
        gw = GatewayFrame(
            network_id=0x01,
            physical_address="123456",
            user_info=b"\x00\x01\x02",
        )
        data = gw.to_bytes()
        assert data[0] == 0xE6  # Gateway header
        assert data[1] == 0x01  # Network ID

    def test_from_bytes_basic(self):
        # Build a valid gateway frame
        gw = GatewayFrame(
            network_id=0x01,
            physical_address="ABC123",
            user_info=b"\x00\x01\x02",
        )
        data = gw.to_bytes()

        # Parse it back
        parsed = GatewayFrame.from_bytes(data)
        assert parsed.network_id == 0x01
        assert parsed.physical_address == "ABC123"

    def test_invalid_header(self):
        with pytest.raises(ValueError, match="Invalid Gateway Frame header"):
            GatewayFrame.from_bytes(b"\x00\x01")

    def test_too_short_frame(self):
        with pytest.raises(ValueError, match="at least 4 bytes"):
            GatewayFrame.from_bytes(b"\xE6\x00")

    def test_wrapper_pdu_property(self):
        gw = GatewayFrame(
            network_id=0x01,
            physical_address="TEST",
            user_info=b"\xAA\xBB",
        )
        wrapper = gw.wrapper_pdu
        assert wrapper[:2] == b'\x00\x01'  # Wrapper header

    def test_physical_address_encoding(self):
        gw = GatewayFrame(physical_address="METR01")
        data = gw.to_bytes()
        # Address should be in the frame
        assert b"METR01" in data


class TestGatewayResponseFrame:
    """Test Gateway Response Frame encoding/decoding."""

    def test_default_frame(self):
        gw = GatewayResponseFrame()
        assert gw.network_id == 0x00
        assert gw.physical_address == ""
        assert gw.user_info == b""

    def test_response_header(self):
        assert GatewayResponseFrame.GATEWAY_RESPONSE_HEADER == 0xE7

    def test_to_bytes_basic(self):
        gw = GatewayResponseFrame(
            network_id=0x02,
            physical_address="RESP01",
            user_info=b"\xFF\xFE",
        )
        data = gw.to_bytes()
        assert data[0] == 0xE7  # Response header
        assert data[1] == 0x02  # Network ID

    def test_from_bytes_basic(self):
        gw = GatewayResponseFrame(
            network_id=0x03,
            physical_address="XYZ789",
            user_info=b"\x10\x20",
        )
        data = gw.to_bytes()
        parsed = GatewayResponseFrame.from_bytes(data)
        assert parsed.network_id == 0x03
        assert parsed.physical_address == "XYZ789"

    def test_invalid_response_header(self):
        with pytest.raises(ValueError, match="Invalid Gateway Response header"):
            GatewayResponseFrame.from_bytes(b"\x00\x01")

    def test_default_wports(self):
        # Response frame has reversed default WPorts
        gw = GatewayResponseFrame()
        assert gw.src_wport == 1  # Meter is source
        assert gw.dst_wport == 16  # Gateway is destination
