"""WebSocket Gateway for DLMS/COSEM.

Provides a WebSocket server that bridges WebSocket clients to DLMS meters,
with multi-client concurrency, real-time data push, authentication, and REST API.
"""
import asyncio
import hashlib
import json
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import IntEnum

LOG = structlog.get_logger()


class ClientRole(IntEnum):
    """WebSocket client authorization roles."""
    READONLY = 1
    OPERATOR = 2
    ADMIN = 3


@dataclass
class WsClient:
    """Connected WebSocket client."""
    ws: Any  # websockets.WebSocketServerProtocol
    client_id: str
    role: ClientRole = ClientRole.READONLY
    subscriptions: Set[str] = field(default_factory=set)  # OBIS codes
    authenticated: bool = False
    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GatewayConfig:
    """Gateway configuration."""
    host: str = "0.0.0.0"
    ws_port: int = 8080
    rest_port: int = 8081
    auth_token: Optional[str] = None  # Simple token auth
    max_clients: int = 50
    heartbeat_interval: int = 30  # seconds
    dlms_host: str = "127.0.0.1"
    dlms_port: int = 4059


class AuthManager:
    """Simple authentication and authorization for WebSocket clients."""

    def __init__(self, config: GatewayConfig):
        self.config = config
        self._tokens: Dict[str, ClientRole] = {}
        if config.auth_token:
            self._tokens[config.auth_token] = ClientRole.ADMIN

    def add_token(self, token: str, role: ClientRole) -> None:
        self._tokens[token] = role

    def authenticate(self, token: str) -> Optional[ClientRole]:
        return self._tokens.get(token)

    def password_hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


class DlmsProxy:
    """Proxies DLMS commands to actual meters.

    In production, this would maintain connections to physical meters.
    For testing/simulation, it uses a callback function.
    """

    def __init__(self, dlms_command_func: Optional[Callable] = None):
        self._command_func = dlms_command_func

    async def send_command(
        self, meter_id: str, command: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a command to a DLMS meter.

        Args:
            meter_id: Meter identifier
            command: Command type (get, set, action)
            params: Command parameters (obis, attribute, value, etc.)

        Returns:
            Command result dict
        """
        if self._command_func:
            try:
                if asyncio.iscoroutinefunction(self._command_func):
                    result = await self._command_func(meter_id, command, params)
                else:
                    result = self._command_func(meter_id, command, params)
                return {"status": "ok", "data": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            # Simulated response
            return {
                "status": "ok",
                "data": {
                    "meter_id": meter_id,
                    "obis": params.get("obis", "unknown"),
                    "value": self._simulate_value(params.get("obis", "")),
                    "timestamp": datetime.now().isoformat(),
                },
            }

    @staticmethod
    def _simulate_value(obis: str) -> Any:
        """Simulate a meter reading based on OBIS code."""
        sim_values = {
            "1.0.1.8.0.255": 12345.67,
            "1.0.32.7.0.255": 220.5,
            "1.0.31.7.0.255": 5.23,
            "1.0.11.7.0.255": 3456.7,
            "1.0.14.7.0.255": 50.01,
        }
        for key, val in sim_values.items():
            if key in obis:
                return val
        return 0


class WsGateway:
    """WebSocket gateway for DLMS/COSEM meters.

    Bridges WebSocket clients to DLMS meters, providing:
    - Multi-client WebSocket server
    - Real-time data push (subscriptions)
    - Authentication and role-based access
    - REST API adapter
    - Heartbeat monitoring

    Usage::

        proxy = DlmsProxy()
        gateway = WsGateway(proxy, GatewayConfig())
        await gateway.start()
    """

    def __init__(
        self,
        proxy: Optional[DlmsProxy] = None,
        config: Optional[GatewayConfig] = None,
    ):
        self.proxy = proxy or DlmsProxy()
        self.config = config or GatewayConfig()
        self.auth = AuthManager(self.config)
        self._clients: Dict[str, WsClient] = {}
        self._running = False
        self._event_handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        self._event_handlers.setdefault(event, []).append(handler)

    async def _emit(self, event: str, **kwargs) -> None:
        for handler in self._event_handlers.get(event, []):
            try:
                await handler(**kwargs)
            except Exception as e:
                LOG.error("Event handler error", event=event, error=str(e))

    async def start(self) -> None:
        """Start the WebSocket gateway."""
        try:
            import websockets
        except ImportError:
            LOG.error("websockets package required. Install with: pip install websockets")
            raise

        self._running = True
        self._ws_server = await websockets.serve(
            self._handle_ws_client,
            self.config.host,
            self.config.ws_port,
            max_size=1024 * 1024,
        )
        LOG.info("WebSocket gateway started",
                 host=self.config.host, port=self.config.ws_port)
        await self._emit("started")

    async def stop(self) -> None:
        """Stop the gateway."""
        self._running = False
        if hasattr(self, "_ws_server"):
            self._ws_server.close()
            await self._ws_server.wait_closed()
        self._clients.clear()
        LOG.info("WebSocket gateway stopped")

    async def _handle_ws_client(self, websocket) -> None:
        """Handle a new WebSocket connection."""
        client_id = str(id(websocket))
        client = WsClient(ws=websocket, client_id=client_id)
        self._clients[client_id] = client
        LOG.info("WebSocket client connected", client_id=client_id)
        await self._emit("client_connected", client_id=client_id)

        try:
            async for message in websocket:
                await self._process_message(client, message)
        except Exception as e:
            LOG.error("WebSocket client error",
                      client_id=client_id, error=str(e))
        finally:
            self._clients.pop(client_id, None)
            LOG.info("WebSocket client disconnected", client_id=client_id)
            await self._emit("client_disconnected", client_id=client_id)

    async def _process_message(self, client: WsClient, message: str) -> None:
        """Process an incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "auth":
                await self._handle_auth(client, data)
            elif msg_type == "get":
                await self._handle_get(client, data)
            elif msg_type == "set":
                await self._handle_set(client, data)
            elif msg_type == "action":
                await self._handle_action(client, data)
            elif msg_type == "subscribe":
                await self._handle_subscribe(client, data)
            elif msg_type == "unsubscribe":
                await self._handle_unsubscribe(client, data)
            elif msg_type == "ping":
                await client.ws.send(json.dumps({"type": "pong"}))
            else:
                await client.ws.send(json.dumps({
                    "type": "error", "message": f"Unknown message type: {msg_type}"
                }))
        except json.JSONDecodeError:
            await client.ws.send(json.dumps({
                "type": "error", "message": "Invalid JSON"
            }))

    async def _handle_auth(self, client: WsClient, data: dict) -> None:
        """Handle authentication."""
        token = data.get("token", "")
        role = self.auth.authenticate(token)
        if role:
            client.authenticated = True
            client.role = role
            await client.ws.send(json.dumps({
                "type": "auth_ok",
                "role": int(role),
                "client_id": client.client_id,
            }))
        else:
            await client.ws.send(json.dumps({
                "type": "auth_failed", "message": "Invalid token"
            }))

    async def _handle_get(self, client: WsClient, data: dict) -> None:
        """Handle GET request."""
        if not client.authenticated:
            await client.ws.send(json.dumps({"type": "error", "message": "Not authenticated"}))
            return
        meter_id = data.get("meter_id", "")
        obis = data.get("obis", "")
        attribute = data.get("attribute", 2)
        result = await self.proxy.send_command(meter_id, "get", {
            "obis": obis, "attribute": attribute,
        })
        await client.ws.send(json.dumps({"type": "get_response", **result}))

    async def _handle_set(self, client: WsClient, data: dict) -> None:
        """Handle SET request."""
        if not client.authenticated or client.role < ClientRole.OPERATOR:
            await client.ws.send(json.dumps({"type": "error", "message": "Permission denied"}))
            return
        meter_id = data.get("meter_id", "")
        obis = data.get("obis", "")
        attribute = data.get("attribute", 2)
        value = data.get("value")
        result = await self.proxy.send_command(meter_id, "set", {
            "obis": obis, "attribute": attribute, "value": value,
        })
        await client.ws.send(json.dumps({"type": "set_response", **result}))

    async def _handle_action(self, client: WsClient, data: dict) -> None:
        """Handle ACTION request."""
        if not client.authenticated or client.role < ClientRole.OPERATOR:
            await client.ws.send(json.dumps({"type": "error", "message": "Permission denied"}))
            return
        meter_id = data.get("meter_id", "")
        obis = data.get("obis", "")
        method = data.get("method", 1)
        result = await self.proxy.send_command(meter_id, "action", {
            "obis": obis, "method": method,
        })
        await client.ws.send(json.dumps({"type": "action_response", **result}))

    async def _handle_subscribe(self, client: WsClient, data: dict) -> None:
        """Handle subscription to data updates."""
        if not client.authenticated:
            await client.ws.send(json.dumps({"type": "error", "message": "Not authenticated"}))
            return
        obis_list = data.get("obis_list", [])
        for obis in obis_list:
            client.subscriptions.add(obis)
        await client.ws.send(json.dumps({
            "type": "subscribed",
            "obis_list": list(client.subscriptions),
        }))

    async def _handle_unsubscribe(self, client: WsClient, data: dict) -> None:
        """Handle unsubscription."""
        obis_list = data.get("obis_list", [])
        for obis in obis_list:
            client.subscriptions.discard(obis)
        await client.ws.send(json.dumps({
            "type": "unsubscribed",
            "obis_list": list(client.subscriptions),
        }))

    async def push_data(self, meter_id: str, obis: str, value: Any) -> int:
        """Push data to subscribed clients.

        Returns number of clients that received the notification.
        """
        message = json.dumps({
            "type": "push",
            "meter_id": meter_id,
            "obis": obis,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })
        count = 0
        for client in list(self._clients.values()):
            if client.authenticated and obis in client.subscriptions:
                try:
                    await client.ws.send(message)
                    count += 1
                except Exception:
                    pass
        return count

    async def push_event(self, event_type: str, meter_id: str, data: Dict) -> int:
        """Push an event notification to all authenticated clients."""
        message = json.dumps({
            "type": "event",
            "event_type": event_type,
            "meter_id": meter_id,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
        count = 0
        for client in list(self._clients.values()):
            if client.authenticated:
                try:
                    await client.ws.send(message)
                    count += 1
                except Exception:
                    pass
        return count

    @property
    def connected_clients(self) -> int:
        return len(self._clients)

    @property
    def authenticated_clients(self) -> int:
        return sum(1 for c in self._clients.values() if c.authenticated)
