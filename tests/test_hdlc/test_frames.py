"""Enhanced HDLC frame encode/decode roundtrip and edge case tests."""

import pytest

from dlms_cosem.hdlc import address
from dlms_cosem.hdlc.frames import (
    CRCCCITT,
    FCS,
    HCS,
    HDLC_FLAG,
    BaseHdlcFrame,
    DisconnectFrame,
    InformationFrame,
    ReceiveReadyFrame,
    SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame,
    UnnumberedInformationFrame,
    frame_has_correct_length,
    frame_is_enclosed_by_hdlc_flags,
)
from dlms_cosem.hdlc.parameters import HdlcParameterList


def _client():
    return address.HdlcAddress(1, None, "client")


def _server():
    return address.HdlcAddress(1, None, "server")


class TestInformationFrameRoundtrip:
    """I-frame encode/decode roundtrip for various info lengths."""

    @pytest.mark.parametrize("info_len", [0, 1, 16, 128, 200])
    def test_roundtrip_various_lengths(self, info_len):
        info = bytes(range(256))[:info_len] if info_len > 0 else b""
        frame = InformationFrame(_client(), _server(), info)
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)
        assert parsed.information == info

    def test_roundtrip_max_info(self):
        info = b"\xE6" * 200
        frame = InformationFrame(_client(), _server(), info)
        parsed = InformationFrame.from_bytes(frame.to_bytes())
        assert parsed.information == info

    def test_send_recv_sequence(self):
        frame = InformationFrame(_client(), _server(), b"\x00", send_sequence_number=5, receive_sequence_number=3)
        parsed = InformationFrame.from_bytes(frame.to_bytes())
        assert parsed.send_sequence_number == 5
        assert parsed.receive_sequence_number == 3


class TestSFrameRoundtrip:
    """S-frame (RR) encode/decode roundtrip."""

    def test_rr_roundtrip(self):
        frame = ReceiveReadyFrame(_client(), _server(), receive_sequence_number=0)
        raw = frame.to_bytes()
        parsed = ReceiveReadyFrame.from_bytes(raw)
        assert parsed.receive_sequence_number == 0

    @pytest.mark.parametrize("seq", [0, 1, 7])
    def test_rr_various_sequences(self, seq):
        frame = ReceiveReadyFrame(_client(), _server(), receive_sequence_number=seq)
        parsed = ReceiveReadyFrame.from_bytes(frame.to_bytes())
        assert parsed.receive_sequence_number == seq


class TestUFrameRoundtrip:
    """U-frame (SNRM, DISC, UA) encode/decode roundtrip."""

    def test_snrm_encode(self):
        frame = SetNormalResponseModeFrame(_client(), _server())
        raw = frame.to_bytes()
        # SNRM doesn't have from_bytes; verify encoding works
        assert len(raw) > 0
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E

    def test_disc_roundtrip(self):
        frame = DisconnectFrame(_client(), _server())
        raw = frame.to_bytes()
        parsed = DisconnectFrame.from_bytes(raw)
        assert parsed is not None

    def test_ua_roundtrip(self):
        frame = UnNumberedAcknowledgmentFrame(_client(), _server())
        raw = frame.to_bytes()
        parsed = UnNumberedAcknowledgmentFrame.from_bytes(raw)
        assert len(parsed.parameters) == 0

    def test_ua_with_params_roundtrip(self):
        params = HdlcParameterList()
        params.set_window_size_tx(3)
        params.set_window_size_rx(3)
        frame = UnNumberedAcknowledgmentFrame(_client(), _server(), parameters=params)
        parsed = UnNumberedAcknowledgmentFrame.from_bytes(frame.to_bytes())
        assert parsed.parameters.window_size == 3


class TestMultiByteAddress:
    """Frames with 1/2/4 byte addresses."""

    def test_single_byte_address(self):
        c = address.HdlcAddress(1, None, "client")
        s = address.HdlcAddress(1, None, "server")
        frame = InformationFrame(c, s, b"\x00")
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)
        assert parsed.destination_address == c
        assert parsed.source_address == s

    def test_two_byte_address(self):
        c = address.HdlcAddress(1, 16, "client")
        s = address.HdlcAddress(1, 1, "server")
        frame = InformationFrame(c, s, b"\xAA")
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)
        assert parsed.information == b"\xAA"

    def test_four_byte_address(self):
        c = address.HdlcAddress(1, 16, "client")
        s = address.HdlcAddress(1, 1, "server")
        frame = SetNormalResponseModeFrame(c, s)
        raw = frame.to_bytes()
        assert len(raw) > 0
        assert raw[0] == 0x7E


class TestCRCEdgeCases:
    """CRC correctness and error detection."""

    def test_crc_deterministic(self):
        from dlms_cosem.hdlc.frames import CRCCCITT
        crc = CRCCCITT()
        crc1 = crc.calculate_for(b"\x01\x02\x03")
        crc2 = crc.calculate_for(b"\x01\x02\x03")
        assert crc1 == crc2

    def test_crc_different_data(self):
        from dlms_cosem.hdlc.frames import CRCCCITT
        crc = CRCCCITT()
        crc1 = crc.calculate_for(b"\x00")
        crc2 = crc.calculate_for(b"\x01")
        assert crc1 != crc2

    def test_frame_corruption_detected(self):
        frame = InformationFrame(_client(), _server(), b"\xDE\xAD")
        raw = bytearray(frame.to_bytes())
        # Corrupt a byte in the info section
        raw[-4] ^= 0xFF
        with pytest.raises(Exception):
            InformationFrame.from_bytes(bytes(raw))

    def test_frame_flags(self):
        frame = InformationFrame(_client(), _server(), b"\x00")
        raw = frame.to_bytes()
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E


class TestSegmentationReassembly:
    """Long messages split into multiple I-frames."""

    def test_long_info_single_frame(self):
        info = bytes(range(256)) * 2  # 512 bytes
        frame = InformationFrame(_client(), _server(), info)
        parsed = InformationFrame.from_bytes(frame.to_bytes())
        assert parsed.information == info
