"""Tests for FEP (Front End Processor) transport."""

import pytest

from dlms_cosem.transport.fep import (
    FepTransport,
    build_fep_connect_pdu,
    build_fep_disconnect_pdu,
    build_fep_get_devices_pdu,
    encode_fep_frame,
    fep_checksum,
    fep_frame_payload_length,
    parse_fep_response,
    parse_get_devices_response,
)


class TestFepChecksum:
    """Test FEP checksum calculation."""

    def test_single_byte(self):
        assert fep_checksum(b'\x01') == 1

    def test_wraps_at_256(self):
        assert fep_checksum(b'\xFF\x01') == 0
        assert fep_checksum(b'\xFF\x02') == 1

    def test_empty(self):
        assert fep_checksum(b'') == 0

    def test_known_values(self):
        data = bytes.fromhex("6882400500200068A10300314156")
        cs = fep_checksum(data)
        assert cs == sum(data) % 256
        assert 0 <= cs <= 255


class TestBuildFepConnectPdu:
    """Test FEP connect PDU construction."""

    def test_basic_structure(self):
        pdu = build_fep_connect_pdu(mst_addr=5, password="314156")
        assert pdu[0] == 0x68
        assert pdu[-1] == 0x16
        assert pdu[4] == 0x05

    def test_checksum_valid(self):
        pdu = build_fep_connect_pdu(mst_addr=5, password="314156")
        assert pdu[-2] == fep_checksum(pdu[:-2])

    def test_contains_connect_command(self):
        pdu = build_fep_connect_pdu(mst_addr=5, password="000000")
        pdu_hex = pdu.hex().upper()
        assert "A10300" in pdu_hex

    def test_different_addresses(self):
        pdu1 = build_fep_connect_pdu(mst_addr=1, password="000000")
        pdu2 = build_fep_connect_pdu(mst_addr=255, password="000000")
        assert pdu1 != pdu2


class TestBuildFepDisconnectPdu:
    """Test FEP disconnect PDU construction."""

    def test_basic_structure(self):
        pdu = build_fep_disconnect_pdu(mst_addr=5)
        assert pdu[0] == 0x68
        assert pdu[-1] == 0x16

    def test_checksum_valid(self):
        pdu = build_fep_disconnect_pdu(mst_addr=5)
        assert pdu[-2] == fep_checksum(pdu[:-2])

    def test_contains_disconnect_command(self):
        pdu = build_fep_disconnect_pdu(mst_addr=5)
        pdu_hex = pdu.hex().upper()
        assert "A20000" in pdu_hex


class TestBuildFepGetDevicesPdu:
    """Test FEP get-devices PDU construction."""

    def test_basic_structure(self):
        pdu = build_fep_get_devices_pdu(mst_addr=5)
        assert pdu[0] == 0x68
        assert pdu[-1] == 0x16

    def test_checksum_valid(self):
        pdu = build_fep_get_devices_pdu(mst_addr=5)
        assert pdu[-2] == fep_checksum(pdu[:-2])


class TestEncodeFepFrame:
    """Test FEP frame encoding."""

    def test_basic_structure(self):
        frame = encode_fep_frame(
            mst_addr=5, meter_no="000000000001",
            apdu=b'\xC0\x01\xC0\x00\x03', src_wport=1, dst_wport=1,
        )
        assert frame[0] == 0x68
        assert frame[-1] == 0x16
        assert frame[-2] == fep_checksum(frame[:-2])

    def test_contains_data_command(self):
        frame = encode_fep_frame(
            mst_addr=5, meter_no="000000000001",
            apdu=b'\xC0\x01', src_wport=1, dst_wport=1,
        )
        cmd_offset = 12  # header(10) + length(2)
        assert frame[cmd_offset] == 0x40
        assert frame[cmd_offset + 1] == 0x7A

    def test_logical_address(self):
        frame = encode_fep_frame(
            mst_addr=5, meter_no="TESTMETER",
            apdu=b'\xC0\x01', src_wport=1, dst_wport=1,
        )
        logical_addr = frame[14:14 + 32]
        assert logical_addr[:9] == b'TESTMETER'
        assert logical_addr[9:] == b'\x00' * 23

    def test_gateway_header(self):
        frame_normal = encode_fep_frame(
            mst_addr=5, meter_no="METER001", apdu=b'\xC0',
            src_wport=1, dst_wport=1, use_gateway=False,
        )
        frame_gw = encode_fep_frame(
            mst_addr=5, meter_no="METER001", apdu=b'\xC0',
            src_wport=1, dst_wport=1, use_gateway=True,
        )
        assert len(frame_gw) > len(frame_normal)
        assert b'\xE6' in frame_gw

    def test_roundtrip_checksum(self):
        frame = encode_fep_frame(
            mst_addr=5, meter_no="000000000001", apdu=b'\xC0\x01',
            src_wport=1, dst_wport=1,
        )
        assert frame[-2] == fep_checksum(frame[:-2])


class TestFepFramePayloadLength:
    """Test FEP frame length calculation."""

    def test_short_data(self):
        assert fep_frame_payload_length(b'\x00' * 5) == 0

    def test_valid_frame(self):
        frame = encode_fep_frame(
            mst_addr=5, meter_no="000000000001", apdu=b'\xC0',
            src_wport=1, dst_wport=1,
        )
        calculated_len = fep_frame_payload_length(frame)
        assert calculated_len == len(frame)

    def test_exact_12_bytes(self):
        raw = b'\x68\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00'
        # payload_len=1, total = 12 + 1 + 2 = 15
        assert fep_frame_payload_length(raw) == 15


class TestParseFepResponse:
    """Test FEP response parsing."""

    def test_short_response(self):
        raw = b'\x68' * 10
        result = parse_fep_response(raw)
        assert result == raw

    def test_strip_gateway(self):
        # Build response matching encode_fep_frame output format
        # header(10) + len_le(2) + cmd(2) + addr(32) + wpdu(14) + gw + apdu + cs(1) + end(1)
        header = bytes.fromhex("6800000005002000682a")  # 10 bytes
        cmd = b'\x40\x7A'  # 2 bytes
        logical_addr = b'000000000001' + b'\x00' * 20  # 32 bytes
        # WPDU: 0001(2) + src(4) + dst(4) + len(4) = 14 bytes
        gw = b'\xE7\x00\x08' + b'METER001'  # 11 bytes
        apdu = b'\xC4\x01\xC0\x00\x02\x06\x00\x00'  # 8 bytes
        wpdu_len = len(gw) + len(apdu)
        wpdu_hdr = b'\x00\x01' + wpdu_len.to_bytes(4, 'big') + wpdu_len.to_bytes(4, 'big')  # 2+4+4=10... no
        # Actually: 0001(2B) + srcWPort(4B hex→2B) + dstWPort(4B hex→2B) + apduLen(4B hex→2B) = hmm
        # Let's use actual hex like encode_fep_frame does:
        apdu_len = len(gw) + len(apdu)
        wpdu_hex = f"0001" + f"{1:08X}" + f"{1:08X}" + f"{apdu_len:08X}"
        wpdu = bytes.fromhex(wpdu_hex)
        payload = cmd + logical_addr + wpdu + gw + apdu
        payload_le = len(payload).to_bytes(2, 'little')
        raw = header + payload_le + payload
        cs = fep_checksum(raw)
        raw += bytes([cs, 0x16])

        result_no_strip = parse_fep_response(raw, strip_gateway=False)
        assert result_no_strip == gw + apdu

        result_strip = parse_fep_response(raw, strip_gateway=True)
        assert result_strip == apdu

    def test_no_gateway(self):
        header = bytes.fromhex("6800000005002000682a")
        cmd = b'\x40\x7A'
        logical_addr = b'000000000001' + b'\x00' * 20
        apdu = b'\xC4\x01\xC0\x00\x02\x06\x00\x00'
        wpdu_hex = f"0001" + f"{1:08X}" + f"{1:08X}" + f"{len(apdu):08X}"
        wpdu = bytes.fromhex(wpdu_hex)
        payload = cmd + logical_addr + wpdu + apdu
        payload_le = len(payload).to_bytes(2, 'little')
        raw = header + payload_le + payload
        cs = fep_checksum(raw)
        raw += bytes([cs, 0x16])

        result = parse_fep_response(raw, strip_gateway=False)
        assert result == apdu


class TestParseGetDevicesResponse:
    """Test FEP device list parsing."""

    def test_empty_response(self):
        assert parse_get_devices_response(b'\x00' * 42) == []

    def test_single_device(self):
        header = b'\x00' * 38
        # Device entry: 50 bytes. Meter "000000000001" in first 32 bytes (ASCII)
        # Use 0x20 (space) as padding so rstrip('0') doesn't eat it
        meter_bytes = b'000000000001' + b' ' * 20  # 32 bytes
        other_bytes = b'\x00' * 18  # 18 bytes
        entry = meter_bytes + other_bytes  # 50 bytes = 100 hex chars
        tail = b'\x00\x00\x00\x16'
        raw = header + entry + tail
        devices = parse_get_devices_response(raw)
        assert len(devices) == 1
        assert "000000000001" in devices[0]

    def test_invalid_length_raises(self):
        header = b'\x00' * 38
        bad_data = b'\x00' * 51  # 102 hex chars, not multiple of 100
        tail = b'\x00\x00\x00\x16'
        raw = header + bad_data + tail
        with pytest.raises(ValueError, match="not multiple of 100"):
            parse_get_devices_response(raw)

    def test_multiple_devices(self):
        header = b'\x00' * 38
        d1 = b'000000000001' + b' ' * 20 + b'\x00' * 18  # 50 bytes
        d2 = b'000000000002' + b' ' * 20 + b'\x00' * 18  # 50 bytes
        tail = b'\x00\x00\x00\x16'
        raw = header + d1 + d2 + tail
        devices = parse_get_devices_response(raw)
        assert len(devices) == 2
        assert "000000000001" in devices[0]
        assert "000000000002" in devices[1]


class TestFepTransport:
    """Test FepTransport class."""

    def test_init_defaults(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        assert transport.mst_addr == 5
        assert transport.meter_no == "000000000001"
        assert transport.src_wport == 1
        assert transport.dst_wport == 1
        assert transport._inner is None

    def test_encode_apdu(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        frame = transport.encode_apdu(b'\xC0\x01')
        assert frame[0] == 0x68
        assert frame[-1] == 0x16

    def test_write_not_connected(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        with pytest.raises(ConnectionError, match="not connected"):
            transport.write(b'\x00')

    def test_read_not_connected(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        with pytest.raises(ConnectionError, match="not connected"):
            transport.read()

    def test_disconnect_not_connected(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        transport.disconnect()  # Should not raise

    def test_inner_property(self):
        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        assert transport.inner is None
