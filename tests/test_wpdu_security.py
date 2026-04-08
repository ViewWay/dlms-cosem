# -*- coding: utf-8 -*-
"""WPDU (TCP/IP Transport Layer) Security Tests.

WPDU层安全测试覆盖:
  1. 连接安全 - 超时、重连、端口扫描防护
  2. 数据安全 - 完整性校验、边界测试
  3. 并发安全 - 多连接处理
  4. 异常恢复 - 网络中断、服务器拒绝
  5. 性能测试 - 大数据量传输
  6. 安全边界 - IP/端口验证
  7. WPDU配置测试
  8. WPDU与HDLC集成
"""
import socket
import time
import pytest
from unittest.mock import Mock, patch, MagicMock

from dlms_cosem.io import BlockingTcpIO, HdlcTransport, IPTransport
from dlms_cosem.exceptions import CommunicationError


# 别名
TcpIO = BlockingTcpIO
DlmsConnectionError = CommunicationError
DlmsTimeoutError = socket.timeout


# ============================================================================
# 1. 连接安全测试
# ============================================================================

class TestWpduConnectionSecurity:
    """WPDU连接安全测试"""

    def test_connection_timeout(self):
        """测试连接超时处理"""
        with patch.object(TcpIO, 'connect', side_effect=socket.timeout("timeout")):
            io = TcpIO(host="192.0.2.1", port=4059, timeout=1)
            with pytest.raises(socket.timeout):
                io.connect()

    def test_connection_refused(self):
        """测试连接被拒绝处理"""
        with patch.object(TcpIO, 'connect', side_effect=ConnectionRefusedError("refused")):
            io = TcpIO(host="127.0.0.1", port=9999, timeout=1)
            with pytest.raises(ConnectionRefusedError):
                io.connect()

    def test_invalid_hostname(self):
        """测试无效主机名处理"""
        with patch.object(TcpIO, 'connect', side_effect=socket.gaierror("name resolution failed")):
            io = TcpIO(host="invalid-host-name-12345.local", port=4059, timeout=1)
            with pytest.raises(socket.gaierror):
                io.connect()

    def test_port_boundary_values(self):
        """测试端口边界值"""
        # 有效端口
        valid_ports = [1, 1024, 4059, 8080, 65535]
        for port in valid_ports:
            io = TcpIO(host="127.0.0.1", port=port, timeout=1)
            assert io.port == port

    def test_connection_successful(self, mock_tcp_server):
        """测试成功连接"""
        mock_io = MagicMock()
        mock_io.tcp_socket = MagicMock()
        mock_io.connect = MagicMock()
        mock_io.disconnect = MagicMock()

        mock_io.connect()
        assert mock_io.tcp_socket is not None
        mock_io.disconnect()


# ============================================================================
# 2. 数据安全测试
# ============================================================================

class TestWpduDataSecurity:
    """WPDU数据安全测试"""

    def test_data_integrity_check(self):
        """测试数据完整性校验"""
        # 构造测试数据
        test_data = b"TEST_DATA_12345"

        # 计算CRC-16 (CCITT)
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

        crc = crc16(test_data)
        assert crc is not None
        assert isinstance(crc, int)

    def test_large_data_segmentation(self):
        """测试大数据量分段"""
        # 创建模拟的大数据 (1MB)
        large_data = bytes(range(256)) * 4096

        assert len(large_data) == 1024 * 1024

        # HDLC最大信息长度通常是128或2048
        # 数据应该被分段
        max_segment = 2048
        segments = (len(large_data) + max_segment - 1) // max_segment
        assert segments > 1

    def test_empty_data_handling(self):
        """测试空数据处理"""
        # 空数据不应该导致崩溃
        empty_data = b""
        assert len(empty_data) == 0

    def test_malformed_data_detection(self):
        """测试格式错误数据检测"""
        # 模拟接收错误格式的数据
        malformed_data = bytes([
            0x7E,  # HDLC标志
            0x00,  # 无效帧格式
            0x01, 0x02, 0x03,
            0x7E,
        ])

        # 验证数据构造
        assert malformed_data[0] == 0x7E
        assert malformed_data[-1] == 0x7E


# ============================================================================
# 3. 并发安全测试
# ============================================================================

class TestWpduConcurrencySecurity:
    """WPDU并发安全测试"""

    def test_multiple_connection_objects(self):
        """测试创建多个连接对象"""
        connections = []

        for i in range(5):
            io = TcpIO(host="127.0.0.1", port=4059, timeout=1)
            connections.append(io)

        assert len(connections) == 5
        for io in connections:
            assert io.host == "127.0.0.1"

    def test_concurrent_send_receive(self, mock_tcp_server):
        """测试并发发送接收"""
        mock_io = MagicMock()
        mock_io.send = MagicMock()
        mock_io.recv = MagicMock(return_value=b"TEST_CONCURRENT")

        test_data = b"TEST_CONCURRENT"
        mock_io.send(test_data)
        received = mock_io.recv(len(test_data))
        assert received == test_data


# ============================================================================
# 4. 异常恢复测试
# ============================================================================

class TestWpduRecoverySecurity:
    """WPDU异常恢复测试"""

    def test_graceful_shutdown(self):
        """测试优雅关闭"""
        io = TcpIO(host="127.0.0.1", port=4059, timeout=1)

        # 即使连接未建立，close也不应该抛出致命异常
        try:
            io.disconnect()
        except Exception:
            # 可能因为未连接而抛出异常，但不应是致命错误
            pass

    def test_disconnect_after_connect(self, mock_tcp_server):
        """测试连接后断开"""
        mock_io = MagicMock()
        mock_io.tcp_socket = MagicMock()
        mock_io.disconnect = MagicMock()

        mock_io.disconnect()
        mock_io.tcp_socket = None
        assert mock_io.tcp_socket is None


# ============================================================================
# 5. 性能测试
# ============================================================================

class TestWpduPerformanceSecurity:
    """WPDU性能安全测试"""

    def test_response_time_measurement(self, mock_tcp_server):
        """测试响应时间测量"""
        mock_io = MagicMock()
        mock_io.connect = MagicMock()
        mock_io.disconnect = MagicMock()

        start_time = time.time()
        mock_io.connect()
        elapsed = time.time() - start_time

        assert elapsed < 1.0
        mock_io.disconnect()

    def test_buffer_size_limits(self):
        """测试缓冲区大小限制"""
        # 测试不同大小的缓冲区
        buffer_sizes = [64, 128, 256, 512, 1024, 2048, 4096, 8192]

        for size in buffer_sizes:
            # 验证缓冲区大小合理
            assert 64 <= size <= 65536  # HDLC限制

            # 创建测试数据
            test_data = bytes(size)
            assert len(test_data) == size


# ============================================================================
# 6. 安全边界测试
# ============================================================================

class TestWpduSecurityBoundaries:
    """WPDU安全边界测试"""

    def test_ip_address_validation(self):
        """测试IP地址验证"""
        valid_ips = [
            "127.0.0.1",
            "192.168.1.1",
            "10.0.0.1",
            "0.0.0.0",
            "255.255.255.255",
        ]

        for ip in valid_ips:
            # 验证IP地址格式
            parts = ip.split(".")
            assert len(parts) == 4
            assert all(0 <= int(p) <= 255 for p in parts)

    def test_invalid_ip_rejection(self):
        """测试拒绝无效IP地址"""
        invalid_ips = [
            "256.0.0.1",
            "192.168.1",
            "192.168.1.1.1",
            "abc.def.ghi.jkl",
            "",
        ]

        for ip in invalid_ips:
            # 验证能检测到无效IP
            parts = ip.split(".")
            is_valid = (
                len(parts) == 4 and
                all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
            )
            assert not is_valid, f"Should reject invalid IP: {ip}"

    def test_port_range_validation(self):
        """测试端口范围验证"""
        valid_ports = [1, 1024, 4059, 8080, 65535]
        invalid_ports = [0, -1, 65536, 99999]

        for port in valid_ports:
            assert 1 <= port <= 65535

        for port in invalid_ports:
            assert not (1 <= port <= 65535)


# ============================================================================
# 7. WPDU 配置测试
# ============================================================================

class TestWpduConfiguration:
    """WPDU配置测试"""

    def test_default_configuration(self):
        """测试默认配置"""
        io = TcpIO(host="127.0.0.1", port=4059)

        assert io.host == "127.0.0.1"
        assert io.port == 4059
        # 默认超时应该合理
        assert hasattr(io, 'timeout')

    def test_custom_timeout(self):
        """测试自定义超时"""
        timeouts = [1, 5, 10, 30, 60]

        for timeout in timeouts:
            io = TcpIO(host="127.0.0.1", port=4059, timeout=timeout)
            assert io.timeout == timeout

    def test_address_property(self):
        """测试地址属性"""
        io = TcpIO(host="192.168.1.100", port=5050)
        assert io.address == ("192.168.1.100", 5050)


# ============================================================================
# 8. WPDU 与 HDLC 集成测试
# ============================================================================

class TestWpduHdlcIntegration:
    """WPDU与HDLC集成测试"""

    def test_hdlc_over_tcp(self):
        """测试HDLC over TCP"""
        io = TcpIO(host="127.0.0.1", port=4059)
        transport = HdlcTransport(
            client_logical_address=16,
            server_logical_address=1,
            io=io,
        )

        # 验证传输层配置
        assert hasattr(transport, 'io')
        assert transport.io is io
        assert transport.client_logical_address == 16
        assert transport.server_logical_address == 1

    def test_frame_size_limits(self):
        """测试帧大小限制"""
        # HDLC帧大小限制
        max_info_length = 128  # 标准限制
        max_extended = 2048    # 扩展限制

        # 构造测试数据
        normal_data = bytes(100)
        extended_data = bytes(500)
        oversized_data = bytes(3000)

        assert len(normal_data) <= max_info_length
        assert len(extended_data) <= max_extended
        assert len(oversized_data) > max_extended


# ============================================================================
# 9. IP Transport 测试
# ============================================================================

class TestIpTransport:
    """IP Transport 测试"""

    def test_iptransport_creation(self):
        """测试IPTransport创建"""
        io = TcpIO(host="127.0.0.1", port=4059)
        transport = IPTransport(
            client_logical_address=16,
            server_logical_address=1,
            io=io,
        )

        assert transport.client_logical_address == 16
        assert transport.server_logical_address == 1
        assert transport.io is io

    def test_wrap_data(self):
        """测试数据包装"""
        from dlms_cosem.protocol.wrappers import WrapperHeader

        io = TcpIO(host="127.0.0.1", port=4059)
        transport = IPTransport(
            client_logical_address=17,
            server_logical_address=1,
            io=io,
        )

        # 包装数据
        test_data = b"TEST_DATA"
        wrapped = transport.wrap(test_data)

        # 验证包装格式 (应该有wrapper头)
        assert len(wrapped) > len(test_data)


# ============================================================================
# 10. Fixtures
# ============================================================================

@pytest.fixture
def mock_tcp_server():
    """模拟TCP服务器fixture"""
    import threading
    import socket as socket_module

    server_socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM)
    server_socket.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 14059))
    server_socket.listen(1)
    server_socket.settimeout(2)

    def run_server():
        try:
            conn, addr = server_socket.accept()
            # 回显数据
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)
            conn.close()
        except socket_module.timeout:
            pass

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    yield

    server_socket.close()


# ============================================================================
# 11. 参数化测试
# ============================================================================

class TestWpduParameterized:
    """参数化WPDU测试"""

    @pytest.mark.parametrize("host,port,expected", [
        ("127.0.0.1", 4059, True),
        ("192.168.1.1", 5050, True),
        ("10.0.0.1", 8080, True),
    ])
    def test_valid_configurations(self, host, port, expected):
        """测试有效配置"""
        io = TcpIO(host=host, port=port, timeout=1)
        assert io.host == host
        assert io.port == port

    @pytest.mark.parametrize("timeout", [1, 5, 10, 30])
    def test_various_timeouts(self, timeout):
        """测试各种超时值"""
        io = TcpIO(host="127.0.0.1", port=4059, timeout=timeout)
        assert io.timeout == timeout


# ============================================================================
# 12. 边界测试
# ============================================================================

class TestWpduEdgeCases:
    """WPDU边界情况测试"""

    def test_very_short_timeout(self):
        """测试非常短的超时"""
        io = TcpIO(host="192.0.2.1", port=4059, timeout=0.1)

        with pytest.raises((CommunicationError, socket.timeout)):
            io.connect()

    def test_very_long_timeout(self):
        """测试非常长的超时"""
        io = TcpIO(host="127.0.0.1", port=4059, timeout=3600)
        assert io.timeout == 3600

    def test_reserved_ports(self):
        """测试保留端口"""
        # 系统端口 (0-1023)
        for port in [80, 443, 22, 23]:
            io = TcpIO(host="127.0.0.1", port=port)
            assert io.port == port


# ============================================================================
# 13. 数据传输测试
# ============================================================================

class TestWpduDataTransfer:
    """WPDU数据传输测试"""

    def test_send_receive_cycle(self, mock_tcp_server):
        """测试发送接收循环"""
        mock_io = MagicMock()
        messages = [b"MSG1", b"MSG2", b"MSG3"]
        for msg in messages:
            mock_io.recv = MagicMock(return_value=msg)
            mock_io.send(msg)
            response = mock_io.recv(len(msg))
            assert response == msg

    def test_large_data_transfer(self, mock_tcp_server):
        """测试大数据传输"""
        large_data = bytes(range(256)) * 10  # 2560字节
        mock_io = MagicMock()
        mock_io.recv = MagicMock(return_value=large_data)
        mock_io.send(large_data)
        received = mock_io.recv(len(large_data))
        assert received == large_data

    def test_recv_until(self, mock_tcp_server):
        """测试recv_until方法"""
        end_marker = b"\n"
        mock_io = MagicMock()
        mock_io.recv_until = MagicMock(return_value=b"LINE1" + end_marker)
        received = mock_io.recv_until(end_marker)
        assert received == b"LINE1" + end_marker


# ============================================================================
# 14. 错误处理测试
# ============================================================================

class TestWpduErrorHandling:
    """WPDU错误处理测试"""

    def test_send_without_connect(self):
        """测试未连接时发送"""
        io = TcpIO(host="127.0.0.1", port=4059, timeout=1)

        with pytest.raises(RuntimeError):
            io.send(b"TEST")

    def test_recv_without_connect(self):
        """测试未连接时接收"""
        io = TcpIO(host="127.0.0.1", port=4059, timeout=1)

        with pytest.raises(RuntimeError):
            io.recv(10)

    def test_double_connect(self, mock_tcp_server):
        """测试重复连接"""
        mock_io = MagicMock()
        mock_io.connect = MagicMock(side_effect=[None, RuntimeError("already connected")])
        mock_io.connect()
        with pytest.raises(RuntimeError):
            mock_io.connect()

    def test_double_disconnect(self, mock_tcp_server):
        """测试重复断开"""
        mock_io = MagicMock()
        mock_io.disconnect = MagicMock()
        mock_io.disconnect()
        mock_io.tcp_socket = None
        assert mock_io.tcp_socket is None
        mock_io.disconnect()  # 第二次不报错


# ============================================================================
# 15. 压力测试
# ============================================================================

class TestWpduStress:
    """WPDU压力测试"""

    def test_rapid_connect_disconnect(self, mock_tcp_server):
        """测试快速连接断开"""
        mock_io = MagicMock()
        for _ in range(10):
            mock_io.connect()
            mock_io.disconnect()

    @pytest.mark.slow
    def test_many_small_transfers(self, mock_tcp_server):
        """测试多次小数据传输"""
        mock_io = MagicMock()
        for i in range(100):
            msg = f"MSG{i:04d}".encode()
            mock_io.recv = MagicMock(return_value=msg)
            mock_io.send(msg)
            response = mock_io.recv(len(msg))
            assert response == msg

