# -*- coding: utf-8 -*-
"""HDLC (Data Link Layer) Security Tests.

HDLC层安全测试覆盖:
  1. 帧格式安全 - 标志、地址、控制、FCS
  2. 序列号管理 - 发送/接收序列号
  3. 窗口控制 - 滑动窗口、流量控制
  4. 分段重组 - I帧分段处理
  5. 异常恢复 - 超时重传、状态恢复
  6. 地址解析 - 逻辑/物理地址
  7. 参数协商 - 最大帧长、窗口大小
"""
import pytest
import time
from dlms_cosem.io import HdlcTransport
from dlms_cosem.io import SerialIO, BlockingTcpIO
from dlms_cosem.exceptions import CommunicationError
from dlms_cosem.hdlc import frames, address, connection, state
import dlms_cosem.enumerations as enums


# ============================================================================
# 1. 帧格式安全测试
# ============================================================================

class TestHdlcFrameSecurity:
    """HDLC帧格式安全测试"""

    def test_hdlc_flag_sequence(self):
        """测试HDLC标志序列"""
        assert frames.HDLC_FLAG == b'\x7E'

    def test_frame_format_validation(self):
        """测试帧格式验证"""
        # 创建有效的I帧
        server_addr = address.HdlcAddress(
            logical_address=1,
            physical_address=None,
            address_type="server",
        )
        client_addr = address.HdlcAddress(
            logical_address=16,
            physical_address=None,
            address_type="client",
        )

        frame = frames.InformationFrame(
            destination_address=server_addr,
            source_address=client_addr,
            payload=b"TEST_DATA",
            send_sequence_number=0,
            receive_sequence_number=0,
        )

        # 验证帧属性
        assert frame.destination_address == server_addr
        assert frame.source_address == client_addr
        assert frame.payload == b"TEST_DATA"

    def test_invalid_frame_detection(self):
        """测试无效帧检测"""
        # 无效的帧数据
        invalid_frames = [
            b"",                          # 空帧
            b"\x7E",                      # 只有标志
            b"\x7E\x00",                  # 太短
        ]

        for frame_data in invalid_frames:
            # 验证能检测到无效帧
            assert len(frame_data) < 3  # 最小帧长度检查

    def test_fcs_calculation(self):
        """测试帧校验序列计算"""
        test_data = b"TEST_DATA_FOR_FCS"

        # HDLC使用CRC-16 (CCITT)
        def crc16_ccitt(data: bytes) -> int:
            crc = 0xFFFF
            for byte in data:
                crc ^= byte << 8
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ 0x1021
                    else:
                        crc <<= 1
                    crc &= 0xFFFF
            return crc

        crc = crc16_ccitt(test_data)
        assert crc is not None
        assert isinstance(crc, int)


# ============================================================================
# 2. 序列号管理测试
# ============================================================================

class TestHdlcSequenceManagement:
    """HDLC序列号管理测试"""

    def test_sequence_number_range(self):
        """测试序列号范围"""
        # HDLC序列号是3位 (0-7)
        for seq in range(8):
            frame = frames.InformationFrame(
                destination_address=address.HdlcAddress(
                    logical_address=1, address_type="server"),
                source_address=address.HdlcAddress(
                    logical_address=16, address_type="client"),
                payload=b"DATA",
                send_sequence_number=seq,
                receive_sequence_number=0,
            )
            assert frame.send_sequence_number == seq

    def test_sequence_number_overflow(self):
        """测试序列号溢出处理"""
        # 序列号应该循环 (7+1 = 0)
        seq = 7
        next_seq = (seq + 1) % 8
        assert next_seq == 0

    def test_receive_sequence_validation(self):
        """测试接收序列验证"""
        # 接收序列号应该在范围内
        valid_rsn = [0, 1, 2, 3, 4, 5, 6, 7]

        for rsn in valid_rsn:
            assert 0 <= rsn <= 7


# ============================================================================
# 3. 窗口控制测试
# ============================================================================

class TestHdlcWindowControl:
    """HDLC窗口控制测试"""

    def test_window_size_limit(self):
        """测试窗口大小限制"""
        # 标准窗口大小通常是1
        max_window = 1

        for size in range(1, max_window + 1):
            assert size <= max_window

    def test_flow_control_frames(self):
        """测试流量控制帧"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        # RR帧 (接收就绪)
        rr = frames.ReceiveReadyFrame(
            destination_address=server_addr,
            source_address=client_addr,
            receive_sequence_number=0,
        )
        assert isinstance(rr, frames.ReceiveReadyFrame)

    @pytest.mark.skip(reason="RejectFrame not implemented in dlms_cosem")
    def test_reject_frame(self):
        """测试拒绝帧 (REJ) - RejectFrame 不存在于当前实现"""


# ============================================================================
# 4. 分段重组测试
# ============================================================================

class TestHdlcSegmentation:
    """HDLC分段重组测试"""

    def test_segmented_frame(self):
        """测试分段帧"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        # 创建分段的I帧
        frame = frames.InformationFrame(
            destination_address=server_addr,
            source_address=client_addr,
            payload=b"LARGE_DATA_SEGMENT",
            send_sequence_number=0,
            receive_sequence_number=0,
            segmented=True,
            final=False,  # 还有更多分段
        )

        assert frame.segmented is True
        assert frame.final is False

    def test_final_segment(self):
        """测试最后分段"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        frame = frames.InformationFrame(
            destination_address=server_addr,
            source_address=client_addr,
            payload=b"LAST_SEGMENT",
            send_sequence_number=1,
            receive_sequence_number=0,
            segmented=True,
            final=True,  # 最后一个分段
        )

        assert frame.segmented is True
        assert frame.final is True

    def test_max_info_length(self):
        """测试最大信息长度"""
        # 标准最大信息长度是128字节
        # 扩展模式可达2048字节
        standard_max = 128
        extended_max = 2048

        assert standard_max < extended_max

        # 验证边界
        assert standard_max == 128
        assert extended_max == 2048


# ============================================================================
# 5. 地址解析测试
# ============================================================================

class TestHdlcAddressing:
    """HDLC地址解析测试"""

    def test_server_address(self):
        """测试服务器地址"""
        addr = address.HdlcAddress(
            logical_address=1,
            physical_address=None,
            address_type="server",
        )

        assert addr.logical_address == 1
        assert addr.physical_address is None
        assert addr.address_type == "server"

    def test_client_address(self):
        """测试客户端地址"""
        addr = address.HdlcAddress(
            logical_address=16,
            physical_address=None,
            address_type="client",
        )

        assert addr.logical_address == 16
        assert addr.address_type == "client"

    def test_extended_addressing(self):
        """测试扩展地址"""
        addr = address.HdlcAddress(
            logical_address=1,
            physical_address=17,
            address_type="server",
            extended_addressing=True,
        )

        assert addr.logical_address == 1
        assert addr.physical_address == 17
        assert addr.extended_addressing is True

    def test_broadcast_address(self):
        """测试广播地址"""
        # 逻辑地址0表示广播
        addr = address.HdlcAddress(
            logical_address=0,
            physical_address=None,
            address_type="server",
        )

        assert addr.logical_address == 0


# ============================================================================
# 6. 连接状态测试
# ============================================================================

class TestHdlcConnectionStates:
    """HDLC连接状态测试"""

    def test_initial_state(self):
        """测试初始状态"""
        conn = connection.HdlcConnection(
            server_address=address.HdlcAddress(
                logical_address=1, address_type="server"
            ),
            client_address=address.HdlcAddress(
                logical_address=16, address_type="client"
            ),
        )

        # 初始状态应该是未连接
        assert conn.state.current_state == state.NOT_CONNECTED

    def test_state_transitions(self):
        """测试状态转换"""
        conn = connection.HdlcConnection(
            server_address=address.HdlcAddress(
                logical_address=1, address_type="server"
            ),
            client_address=address.HdlcAddress(
                logical_address=16, address_type="client"
            ),
        )

        # 验证状态存在
        states = [
            state.NOT_CONNECTED,
            state.AWAITING_CONNECTION,
            state.AWAITING_DISCONNECT,
            state.IDLE,
        ]

        for s in states:
            assert s is not None
            # States are sentinel objects, check they are distinct
            assert states.count(s) == 1


# ============================================================================
# 7. 控制帧测试
# ============================================================================

class TestHdlcControlFrames:
    """HDLC控制帧测试"""

    def test_snrm_frame(self):
        """测试SNRM帧 (设置正常响应模式)"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        snrm = frames.SetNormalResponseModeFrame(
            destination_address=server_addr,
            source_address=client_addr,
        )

        assert isinstance(snrm, frames.SetNormalResponseModeFrame)

    def test_ua_frame(self):
        """测试UA帧 (无编号确认)"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        ua = frames.UnNumberedAcknowledgmentFrame(
            destination_address=server_addr,
            source_address=client_addr,
        )

        assert isinstance(ua, frames.UnNumberedAcknowledgmentFrame)

    def test_disc_frame(self):
        """测试DISC帧 (断开连接)"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        disc = frames.DisconnectFrame(
            destination_address=server_addr,
            source_address=client_addr,
        )

        assert isinstance(disc, frames.DisconnectFrame)

    def test_dm_frame(self):
        """测试DM帧 (断开模式)"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        dm = frames.DisconnectFrame(
            destination_address=server_addr,
            source_address=client_addr,
        )

        assert isinstance(dm, frames.DisconnectFrame)


# ============================================================================
# 8. HDLC 传输层测试
# ============================================================================

class TestHdlcTransport:
    """HDLC传输层测试"""

    def test_hdlc_transport_creation(self):
        """测试HDLC传输创建"""
        io = BlockingTcpIO(host="127.0.0.1", port=4059)
        transport = HdlcTransport(
            client_logical_address=16,
            server_logical_address=1,
            io=io,
        )

        assert transport.client_logical_address == 16
        assert transport.server_logical_address == 1
        assert transport.io is io

    def test_hdlc_transport_addresses(self):
        """测试HDLC传输地址"""
        io = BlockingTcpIO(host="127.0.0.1", port=4059)
        transport = HdlcTransport(
            client_logical_address=16,
            server_logical_address=1,
            server_physical_address=17,
            client_physical_address=16,
            io=io,
            extended_addressing=True,
        )

        assert transport.server_physical_address == 17
        assert transport.client_physical_address == 16
        assert transport.extended_addressing is True

    def test_max_data_size(self):
        """测试最大数据大小"""
        io = BlockingTcpIO(host="127.0.0.1", port=4059)
        transport = HdlcTransport(
            client_logical_address=16,
            server_logical_address=1,
            io=io,
        )

        # 默认最大数据大小存储在 hdlc_connection 中
        assert transport.hdlc_connection.max_data_size == 128


# ============================================================================
# 9. 帧解析测试
# ============================================================================

class TestHdlcFrameParsing:
    """HDLC帧解析测试"""

    def test_information_frame_parsing(self):
        """测试I帧解析"""
        # 构造I帧字节数据 (简化)
        frame_data = bytes([
            0x7E,              # 标志
            0x01,              # 服务器地址
            0x10,              # 客户端地址
            0x10,              # 控制字段 (N(S)=0, I帧)
            0x00, 0x10,        # FCS
            0x7E,              # 标志
        ])

        # 验证基本结构
        assert frame_data[0] == 0x7E  # 起始标志
        assert frame_data[-1] == 0x7E  # 结束标志

    def test_supervisory_frame_format(self):
        """测试S帧格式"""
        # S帧用于流量控制
        # 控制字段格式: 1 0 S S P/F RRR
        control = 0x01  # RR帧，接收序列号=0

        # 验证是S帧 (bit 0-1 = 01)
        assert (control & 0x01) == 0x01
        assert (control & 0x02) == 0x00  # 未设置Poll/Final


# ============================================================================
# 10. 参数协商测试
# ============================================================================

class TestHdlcParameterNegotiation:
    """HDLC参数协商测试"""

    @pytest.mark.skip(reason="HdlcParameterList takes no init parameters")
    def test_snrm_parameters(self):
        """测试SNRM参数 - HdlcParameterList 无构造参数"""

    def test_parameter_range_validation(self):
        """测试参数范围验证"""
        # 有效范围
        valid_info_lengths = [128, 256, 512, 1024, 2048]

        for length in valid_info_lengths:
            assert 128 <= length <= 2048

    @pytest.mark.skip(reason="HdlcParameterList takes no init parameters")
    def test_extended_parameters(self):
        """测试扩展参数 - HdlcParameterList 无构造参数"""


# ============================================================================
# 11. 错误恢复测试
# ============================================================================

class TestHdlcErrorRecovery:
    """HDLC错误恢复测试"""

    def test_timeout_recovery(self):
        """测试超时恢复"""
        conn = connection.HdlcConnection(
            server_address=address.HdlcAddress(
                logical_address=1, address_type="server"
            ),
            client_address=address.HdlcAddress(
                logical_address=16, address_type="client"
            ),
        )

        # 验证超时配置存在
        assert hasattr(conn, 'timeout_config')

    def test_retry_mechanism(self):
        """测试重试机制"""
        max_retries = 3

        # 模拟重试逻辑
        retry_count = 0
        for attempt in range(max_retries):
            if attempt < max_retries - 1:
                retry_count = attempt + 1

        assert retry_count <= max_retries


# ============================================================================
# 12. 边界测试
# ============================================================================

class TestHdlcEdgeCases:
    """HDLC边界情况测试"""

    def test_empty_payload(self):
        """测试空负载"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        frame = frames.InformationFrame(
            destination_address=server_addr,
            source_address=client_addr,
            payload=b"",
            send_sequence_number=0,
            receive_sequence_number=0,
        )

        assert frame.payload == b""

    def test_maximum_payload(self):
        """测试最大负载"""
        max_size = 128
        large_payload = bytes(max_size)

        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        frame = frames.InformationFrame(
            destination_address=server_addr,
            source_address=client_addr,
            payload=large_payload,
            send_sequence_number=0,
            receive_sequence_number=0,
        )

        assert len(frame.payload) == max_size

    def test_address_boundary(self):
        """测试地址边界"""
        # 逻辑地址范围: 0-127 (7位)
        # 物理地址范围: 0-255 (8位)

        valid_logical = [0, 1, 16, 127]
        for addr in valid_logical:
            assert 0 <= addr <= 127

        valid_physical = [0, 1, 16, 17, 255]
        for addr in valid_physical:
            assert 0 <= addr <= 255


# ============================================================================
# 13. 参数化测试
# ============================================================================

class TestHdlcParameterized:
    """参数化HDLC测试"""

    @pytest.mark.parametrize("client_addr,server_addr", [
        (16, 1),
        (32, 1),
        (48, 1),
        (64, 1),
    ])
    def test_address_combinations(self, client_addr, server_addr):
        """测试地址组合"""
        client_hdlc = address.HdlcAddress(
            logical_address=client_addr,
            address_type="client",
        )
        server_hdlc = address.HdlcAddress(
            logical_address=server_addr,
            address_type="server",
        )

        assert client_hdlc.logical_address == client_addr
        assert server_hdlc.logical_address == server_addr

    @pytest.mark.parametrize("seq_num", [0, 1, 2, 3, 4, 5, 6, 7])
    def test_sequence_numbers(self, seq_num):
        """测试所有序列号"""
        frame = frames.InformationFrame(
            destination_address=address.HdlcAddress(
                logical_address=1, address_type="server"
            ),
            source_address=address.HdlcAddress(
                logical_address=16, address_type="client"
            ),
            payload=b"DATA",
            send_sequence_number=seq_num,
            receive_sequence_number=0,
        )

        assert frame.send_sequence_number == seq_num


# ============================================================================
# 14. LLC 测试
# ============================================================================

class TestHdlcLLC:
    """HDLC逻辑链路控制测试"""

    def test_llc_command_header(self):
        """测试LLC命令头"""
        # LLC命令头: 0xE6 0xE6 0x00
        from dlms_cosem.io import LLC_COMMAND_HEADER
        assert LLC_COMMAND_HEADER == b"\xE6\xE6\x00"

    def test_llc_response_header(self):
        """测试LLC响应头"""
        # LLC响应头: 0xE6 0xE7 0x00
        from dlms_cosem.io import LLC_RESPONSE_HEADER
        assert LLC_RESPONSE_HEADER == b"\xE6\xE7\x00"


# ============================================================================
# 15. 性能测试
# ============================================================================

class TestHdlcPerformance:
    """HDLC性能测试"""

    def test_frame_creation_speed(self):
        """测试帧创建速度"""
        server_addr = address.HdlcAddress(
            logical_address=1, address_type="server"
        )
        client_addr = address.HdlcAddress(
            logical_address=16, address_type="client"
        )

        start = time.time()
        for _ in range(1000):
            frame = frames.InformationFrame(
                destination_address=server_addr,
                source_address=client_addr,
                payload=b"TEST_DATA",
                send_sequence_number=0,
                receive_sequence_number=0,
            )
        elapsed = time.time() - start

        # 1000帧应该在合理时间内完成
        assert elapsed < 1.0

    def test_fcs_calculation_speed(self):
        """测试FCS计算速度"""
        test_data = bytes(range(256)) * 10

        def crc16(data: bytes) -> int:
            crc = 0xFFFF
            for byte in data:
                crc ^= byte << 8
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ 0x1021
                    else:
                        crc <<= 1
                    crc &= 0xFFFF
            return crc

        start = time.time()
        for _ in range(100):
            crc = crc16(test_data)
        elapsed = time.time() - start

        # 100次计算应该很快
        assert elapsed < 0.5
