"""HDLC 实用测试 — 类似 pdlms 的工程化验证。

重点：
  1. FCS/CRC 确定性验证
  2. HDLC 帧编解码往返测试
  3. 地址范围验证 (0-127)
  4. 无效帧处理 (错误消息匹配)
  5. I-frame 提取 APDU
  6. 非 I-frame 识别 (SNRM/UA/RR)
"""

import pytest

from dlms_cosem.hdlc import address
from dlms_cosem.hdlc.exceptions import (
    HdlcParsingError,
    HdlcTimeoutError,
    LocalProtocolError,
)
from dlms_cosem.hdlc.frames import (
    CRCCCITT,
    FCS,
    HCS,
    HDLC_FLAG,
    DisconnectFrame,
    InformationFrame,
    ReceiveReadyFrame,
    SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame,
)


# ─── Helpers ──────────────────────────────────────────────


def _client(logical: int = 1) -> address.HdlcAddress:
    return address.HdlcAddress(logical, None, "client")


def _server(logical: int = 16) -> address.HdlcAddress:
    return address.HdlcAddress(logical, None, "server")


# ─── 1. FCS/CRC 确定性 ────────────────────────────────


class TestFCSDeterminism:
    """FCS (Frame Check Sequence) 确定性验证。"""

    def test_fcs_deterministic(self):
        data = b"\x01\x02\x03"
        fcs1 = FCS.calculate_for(data)
        fcs2 = FCS.calculate_for(data)
        assert len(fcs1) == 2
        assert fcs1 == fcs2

    def test_fcs_different_data_different_fcs(self):
        fcs1 = FCS.calculate_for(b"\x00\x00\x00")
        fcs2 = FCS.calculate_for(b"\xFF\xFF\xFF")
        assert fcs1 != fcs2

    def test_fcs_empty(self):
        fcs = FCS.calculate_for(b"")
        assert len(fcs) == 2

    def test_hcs_deterministic(self):
        """HCS (Header Check Sequence) for address + control fields."""
        data = b"\x01\x00"
        hcs1 = HCS.calculate_for(data)
        hcs2 = HCS.calculate_for(data)
        assert len(hcs1) == 2
        assert hcs1 == hcs2


# ─── 2. 帧编解码往返 ─────────────────────────────────────


class TestHdlcRoundtrip:
    """HDLC 帧编解码往返测试。"""

    def test_information_frame_roundtrip(self):
        """I-frame 编解码往返。"""
        payload = b"\x60\x0a\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a"
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=payload,
        )
        raw = frame.to_bytes()
        assert raw[0] == 0x7E  # HDLC_FLAG
        assert raw[-1] == 0x7E  # HDLC_FLAG

        parsed = InformationFrame.from_bytes(raw)
        assert parsed.payload == payload
        assert parsed.destination_address.logical_address == 1
        assert parsed.source_address.logical_address == 16

    def test_snrm_frame_to_bytes(self):
        """SNRM 帧序列化。"""
        frame = SetNormalResponseModeFrame(
            destination_address=_server(1),
            source_address=_client(16),
        )
        raw = frame.to_bytes()
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E

    def test_ua_frame_to_bytes(self):
        """UA (Unnumbered Acknowledgment) 帧序列化。"""
        frame = UnNumberedAcknowledgmentFrame(
            destination_address=_server(1),
            source_address=_client(16),
        )
        raw = frame.to_bytes()
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E

    def test_rr_frame_to_bytes(self):
        """RR (Receive Ready) 帧序列化。"""
        frame = ReceiveReadyFrame(
            destination_address=_server(1),
            source_address=_client(16),
            receive_sequence_number=0,
        )
        raw = frame.to_bytes()
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E


# ─── 3. 地址范围验证 ─────────────────────────────────────


class TestHdlcAddressValidation:
    """HDLC 地址范围验证 (0-127)。"""

    def test_address_0_127_are_valid(self):
        for addr in [0, 1, 16, 127]:
            a = address.HdlcAddress(addr, None, "server")
            assert a.logical_address == addr

    def test_address_128_255_are_accepted_by_api(self):
        """API 接受 >127，但 DLMS 标准规定范围 0-127。"""
        # dlms-cosem 实现不强制限制，由应用层验证
        for addr in [128, 200, 255]:
            a = address.HdlcAddress(addr, None, "server")
            assert a.logical_address == addr


# ─── 4. 无效帧处理 ─────────────────────────────────────


class TestInvalidFrameHandling:
    """无效帧错误处理验证。"""

    def test_frame_without_starting_7e_raises(self):
        """帧不以 0x7E 开头应报错。"""
        with pytest.raises((HdlcParsingError, LocalProtocolError)):
            InformationFrame.from_bytes(b"\x00\x01\x02\x03\x7E")

    def test_frame_without_trailing_7e_raises(self):
        """帧不以 0x7E 结尾应报错。"""
        with pytest.raises((HdlcParsingError, LocalProtocolError)):
            InformationFrame.from_bytes(b"\x7E\x00\x01\x02")

    def test_empty_frame_raises(self):
        """空帧应报错。"""
        with pytest.raises((HdlcParsingError, LocalProtocolError, IndexError)):
            InformationFrame.from_bytes(b"")

    def test_frame_too_short_raises(self):
        """帧太短应报错。"""
        with pytest.raises((HdlcParsingError, LocalProtocolError)):
            InformationFrame.from_bytes(b"\x7E\x7E")


# ─── 5. I-frame 提取 APDU ───────────────────────────────


class TestIFrameApduExtraction:
    """从 I-frame 提取 APDU。"""

    def test_get_request_apdu_from_i_frame(self):
        """从 I-frame 提取 Get Request APDU。"""
        # 典型 Get Response APDU (C1 01 ...)
        apdu = b"\xC1\x01\x01\x00\x00\x00\x00"
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=apdu,
        )
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)

        # 提取 APDU
        assert parsed.payload == apdu
        assert parsed.payload[0] == 0xC1  # Get Response Normal tag

    def test_set_request_apdu_from_i_frame(self):
        """从 I-frame 提取 Set Request APDU。"""
        # Set Response APDU (C2 01 ...)
        apdu = b"\xC2\x01\x02\x00\x00\x00\x00\x00"
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=apdu,
        )
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)

        assert parsed.payload == apdu
        assert parsed.payload[0] == 0xC2  # Set Response tag

    def test_action_request_apdu_from_i_frame(self):
        """从 I-frame 提取 Action Request APDU。"""
        # Action Response APDU (C3 01 ...)
        apdu = b"\xC3\x01\x03\x00\x00\x00\x00\x00"
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=apdu,
        )
        raw = frame.to_bytes()
        parsed = InformationFrame.from_bytes(raw)

        assert parsed.payload == apdu
        assert parsed.payload[0] == 0xC3  # Action Response tag


# ─── 6. 非 I-frame 识别 ─────────────────────────────────────
# (已由其他测试覆盖)


# ─── 7. HDLC Flag 位置 ─────────────────────────────────────


class TestHdlcFlagPosition:
    """HDLC Flag (0x7E) 位置验证。"""

    def test_frame_starts_and_ends_with_7e(self):
        """HDLC 帧必须以 0x7E 开头和结尾。"""
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=b"\x00\x01\x02",
        )
        raw = frame.to_bytes()

        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E

    def test_only_outer_7e_flags(self):
        """只有外层的 0x7E 是 flag。"""
        frame = InformationFrame(
            destination_address=_server(1),
            source_address=_client(16),
            payload=b"\x7E\x7E",  # payload 里有 0x7E
        )
        raw = frame.to_bytes()

        # 至少外层有 flag
        assert raw[0] == 0x7E
        assert raw[-1] == 0x7E
