"""Tests for async DLMS client."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dlms_cosem.async_client import (
    AsyncDlmsClient, AsyncClientConfig, AsyncHDLCConnection,
    ConnectionState, RetryConfig,
)


class TestAsyncClientConfig:
    def test_default_config(self):
        cfg = AsyncClientConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 4059
        assert cfg.timeout == 10.0

    def test_retry_config(self):
        retry = RetryConfig(max_retries=5, base_delay=0.5)
        assert retry.max_retries == 5
        assert retry.backoff_factor == 2.0


class TestAsyncHDLCConnection:
    def test_connect(self):
        async def _run():
            cfg = AsyncClientConfig()
            conn = AsyncHDLCConnection(cfg)
            mock_reader = AsyncMock()
            mock_writer = MagicMock()
            mock_writer.drain = AsyncMock()
            with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
                await conn.connect()
                assert conn.connected
        asyncio.run(_run())

    def test_disconnect(self):
        async def _run():
            cfg = AsyncClientConfig()
            conn = AsyncHDLCConnection(cfg)
            conn._writer = MagicMock()
            conn._writer.close = MagicMock()
            conn._writer.wait_closed = AsyncMock()
            conn._connected = True
            await conn.disconnect()
            assert not conn.connected
        asyncio.run(_run())

    def test_send_not_connected(self):
        async def _run():
            cfg = AsyncClientConfig()
            conn = AsyncHDLCConnection(cfg)
            try:
                await conn.send(b"data")
                assert False, "should raise"
            except Exception:
                pass
        asyncio.run(_run())

    def test_recv_not_connected(self):
        async def _run():
            cfg = AsyncClientConfig()
            conn = AsyncHDLCConnection(cfg)
            try:
                await conn.recv(1024)
                assert False, "should raise"
            except Exception:
                pass
        asyncio.run(_run())

    def test_send_recv(self):
        async def _run():
            cfg = AsyncClientConfig()
            conn = AsyncHDLCConnection(cfg)
            mock_reader = AsyncMock()
            mock_writer = MagicMock()
            mock_writer.drain = AsyncMock()
            conn._reader = mock_reader
            conn._writer = mock_writer
            conn._connected = True
            await conn.send(b"test")
            mock_writer.write.assert_called_once_with(b"test")
            mock_reader.read = AsyncMock(return_value=b"resp")
            result = await conn.recv(4)
            assert result == b"resp"
        asyncio.run(_run())


class TestAsyncDlmsClient:
    def test_connect(self):
        async def _run():
            cfg = AsyncClientConfig()
            client = AsyncDlmsClient(cfg)
            client._hdlc = AsyncMock()
            client._hdlc.connect = AsyncMock()
            await client.connect()
            assert client.state == ConnectionState.CONNECTED_HDLC
        asyncio.run(_run())

    def test_connect_failure(self):
        async def _run():
            cfg = AsyncClientConfig(timeout=0.1)
            client = AsyncDlmsClient(cfg)
            client._hdlc = AsyncMock()
            client._hdlc.connect = AsyncMock(side_effect=asyncio.TimeoutError())
            try:
                await client.connect()
                assert False
            except Exception:
                pass
            assert client.state == ConnectionState.DISCONNECTED
        asyncio.run(_run())

    def test_disconnect(self):
        async def _run():
            client = AsyncDlmsClient()
            client._hdlc = AsyncMock()
            client._hdlc.disconnect = AsyncMock()
            client._hdlc.connected = True
            client._state = ConnectionState.ASSOCIATED
            await client.disconnect()
            assert client.state == ConnectionState.DISCONNECTED
        asyncio.run(_run())

    def test_get_not_associated(self):
        async def _run():
            client = AsyncDlmsClient()
            client._state = ConnectionState.DISCONNECTED
            from dlms_cosem.cosem.obis import Obis
            try:
                await client.get(Obis("0.0.1.0.0.255"))
                assert False
            except Exception:
                pass
        asyncio.run(_run())

    def test_context_manager(self):
        async def _run():
            client = AsyncDlmsClient()
            client.connect = AsyncMock()
            client.disconnect = AsyncMock()
            async with client as c:
                assert c is client
            client.disconnect.assert_called_once()
        asyncio.run(_run())

    def test_send_with_retry(self):
        async def _run():
            client = AsyncDlmsClient(AsyncClientConfig(retry=RetryConfig(max_retries=3, base_delay=0.01)))
            client._hdlc = AsyncMock()
            client._hdlc.send = AsyncMock(side_effect=OSError("fail"))
            try:
                await client._send_with_retry(b"data")
                assert False
            except Exception:
                pass
            assert client._hdlc.send.call_count == 3
        asyncio.run(_run())

    def test_strip_hdlc(self):
        result = AsyncDlmsClient._strip_hdlc(b"\x7e\xa0\x01\x7e")
        assert result == b"\xa0\x01"

    def test_connection_states(self):
        assert ConnectionState.DISCONNECTED == 0
        assert ConnectionState.CONNECTING == 1
        assert ConnectionState.CONNECTED_HDLC == 2
        assert ConnectionState.ASSOCIATED == 3
