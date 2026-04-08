"""MockTransport 测试 — 验证 mock 传输层功能。"""

import pytest

from tests.conftest import MockTransport


def test_mock_transport_records_sent_bytes():
    """MockTransport 记录所有发送的字节。"""
    mt = MockTransport()
    mt.send(b"\x01\x02\x03")
    mt.send(b"\x04\x05\x06")

    assert len(mt.sent) == 2
    assert mt.sent[0] == b"\x01\x02\x03"
    assert mt.sent[1] == b"\x04\x05\x06"


def test_mock_transport_returns_queued_responses():
    """MockTransport 按顺序返回预设响应。"""
    mt = MockTransport([b"\xAA", b"\xBB"])

    assert mt.send(b"req1") == b"\xAA"
    assert mt.send(b"req2") == b"\xBB"
    assert mt.send(b"req3") == b""  # 队列空后返回空


def test_mock_transport_enqueue_response():
    """enqueue_response 动态追加响应到队列。"""
    mt = MockTransport()

    mt.enqueue_response(b"\xCC")
    mt.enqueue_response(b"\xDD")

    assert mt.send(b"req1") == b"\xCC"
    assert mt.send(b"req2") == b"\xDD"


def test_mock_transport_initial_empty():
    """新 MockTransport 默认队列为空。"""
    mt = MockTransport()

    assert mt._responses == []
    assert mt.send(b"req") == b""


def test_mock_transport_with_initial_responses():
    """构造时传入初始响应列表。"""
    mt = MockTransport([b"resp1", b"resp2"])

    assert len(mt._responses) == 2
    assert mt.send(b"req1") == b"resp1"
    assert mt._responses == [b"resp2"]


def test_mock_transport_empty_after_dequeue():
    """响应取完后队列为空。"""
    mt = MockTransport([b"only"])

    assert len(mt._responses) == 1
    mt.send(b"req")
    assert len(mt._responses) == 0


def test_mock_transport_connect_disconnect_noop():
    """connect/disconnect 无操作（mock 传输不需要实际连接）。"""
    mt = MockTransport()
    mt.connect()
    mt.disconnect()
    # 不应抛出异常


def test_mock_transport_default_addresses():
    """默认逻辑地址：client=16, server=1。"""
    mt = MockTransport()
    assert mt.client_logical_address == 16
    assert mt.server_logical_address == 1
    assert mt.timeout == 10
