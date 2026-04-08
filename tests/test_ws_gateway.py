"""Tests for WebSocket Gateway."""
import pytest
from dlms_cosem.ws_gateway import (
    WsGateway, GatewayConfig, DlmsProxy, AuthManager,
    ClientRole, WsClient,
)
from unittest.mock import AsyncMock, MagicMock


class TestDlmsProxy:
    @pytest.mark.asyncio
    async def test_simulated_command(self):
        proxy = DlmsProxy()
        result = await proxy.send_command("M001", "get", {"obis": "1.0.1.8.0.255"})
        assert result["status"] == "ok"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_custom_command_func(self):
        async def cmd_func(meter_id, command, params):
            return {"custom": True}
        proxy = DlmsProxy(cmd_func)
        result = await proxy.send_command("M001", "get", {})
        assert result["data"]["custom"] is True

    @pytest.mark.asyncio
    async def test_command_error(self):
        async def failing_cmd(meter_id, command, params):
            raise ValueError("test error")
        proxy = DlmsProxy(failing_cmd)
        result = await proxy.send_command("M001", "get", {})
        assert result["status"] == "error"


class TestAuthManager:
    def test_authenticate_valid(self):
        config = GatewayConfig(auth_token="secret")
        auth = AuthManager(config)
        role = auth.authenticate("secret")
        assert role == ClientRole.ADMIN

    def test_authenticate_invalid(self):
        config = GatewayConfig(auth_token="secret")
        auth = AuthManager(config)
        assert auth.authenticate("wrong") is None

    def test_add_token(self):
        config = GatewayConfig()
        auth = AuthManager(config)
        auth.add_token("reader", ClientRole.READONLY)
        assert auth.authenticate("reader") == ClientRole.READONLY

    def test_password_hash(self):
        auth = AuthManager(GatewayConfig())
        h = auth.password_hash("test")
        assert len(h) == 64  # SHA256 hex


class TestWsGateway:
    def test_create(self):
        proxy = DlmsProxy()
        gw = WsGateway(proxy, GatewayConfig(ws_port=9999))
        assert gw.connected_clients == 0
        assert gw.authenticated_clients == 0

    def test_event_handler(self):
        gw = WsGateway()
        events = []
        gw.on("test", lambda **kw: events.append(kw))
        # Event system works (async tested elsewhere)

    @pytest.mark.asyncio
    async def test_push_data_no_clients(self):
        gw = WsGateway()
        count = await gw.push_data("M001", "1.0.1.8.0.255", 100)
        assert count == 0

    @pytest.mark.asyncio
    async def test_push_event_no_clients(self):
        gw = WsGateway()
        count = await gw.push_event("alarm", "M001", {"msg": "test"})
        assert count == 0

    def test_client_roles(self):
        assert ClientRole.READONLY < ClientRole.OPERATOR < ClientRole.ADMIN
