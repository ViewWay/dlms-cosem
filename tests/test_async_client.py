"""Tests for AsyncDlmsClient."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from dlms_cosem import cosem, enumerations
from dlms_cosem.async_client import AsyncDlmsClient
from dlms_cosem.security import NoSecurityAuthentication


def _make_client(**kwargs) -> AsyncDlmsClient:
    transport = MagicMock()
    auth = NoSecurityAuthentication()
    return AsyncDlmsClient(
        transport=transport,
        authentication=auth,
        **kwargs,
    )


def _make_cosem_attribute():
    return cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=cosem.Obis(1, 0, 0, 1, 0, 255),
        attribute=2,
    )


class TestAsyncDlmsClientInit:
    def test_instantiation(self):
        client = _make_client()
        assert client.invoke_id == 0
        assert client.timeout == 10
        assert client.dlms_connection is not None

    def test_custom_params(self):
        client = _make_client(timeout=30, max_pdu_size=1024)
        assert client.timeout == 30
        assert client.max_pdu_size == 1024


class TestAsyncDlmsClientInvokeId:
    def test_next_invoke_id(self):
        client = _make_client()
        assert client.next_invoke_id() == 0
        assert client.next_invoke_id() == 1
        assert client.next_invoke_id() == 2


class TestAsyncConnect:
    @pytest.mark.asyncio
    async def test_connect_calls_transport(self):
        client = _make_client()
        await client.connect()
        client.transport.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_calls_transport(self):
        client = _make_client()
        await client.disconnect()
        client.transport.disconnect.assert_called_once()


class TestAsyncClose:
    @pytest.mark.asyncio
    async def test_close_releases_and_disconnects(self):
        client = _make_client()
        client.dlms_connection.get_rlrq = MagicMock(return_value=MagicMock())
        await client.close()
        client.transport.disconnect.assert_called()


class TestConcurrentGet:
    @pytest.mark.asyncio
    async def test_concurrent_gets_are_serialized(self):
        """Multiple concurrent get calls should be serialized by the lock."""
        client = _make_client()
        call_order = []
        send_count = 0

        # Override the entire send method to avoid touching dlms_connection internals
        async def mock_send(*events):
            nonlocal send_count
            call_order.append(("send", send_count))
            send_count += 1

        # Override next_event to return a valid GetResponseNormal
        from dlms_cosem.protocol.xdlms import GetResponseNormal, InvokeIdAndPriority
        response = GetResponseNormal(
            data=b"\x01\x02\x03",
            invoke_id_and_priority=InvokeIdAndPriority(0, True, True),
        )

        client.send = mock_send
        client.next_event = lambda: response

        async def do_get(n):
            attr = _make_cosem_attribute()
            await client.get(attr)
            call_order.append(("done", n))

        await asyncio.gather(do_get(0), do_get(1), do_get(2))

        assert send_count == 3
        assert len(call_order) == 6


class TestAsyncCancel:
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Verify a cancelled asyncio task propagates CancelledError."""
        async def long_op():
            await asyncio.sleep(100)

        task = asyncio.create_task(long_op())
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


class TestSessionContextManager:
    @pytest.mark.asyncio
    async def test_session_context(self):
        from dlms_cosem.async_client import _AsyncSession

        client = _make_client()

        async def noop():
            pass

        client.connect = noop
        client.disconnect = noop
        client.associate = noop
        client.release_association = noop

        sess = _AsyncSession(client)
        assert sess._client is client
        result = await sess.__aenter__()
        assert result is client
        await sess.__aexit__(None, None, None)


class TestImport:
    def test_import_from_package(self):
        from dlms_cosem import AsyncDlmsClient as ADC
        assert ADC is AsyncDlmsClient
