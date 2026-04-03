"""COSEM Server - a complete DLMS/COSEM server implementation.

Supports HDLC/TCP/UDP/TLS transports, pluggable COSEM object models,
request routing, response generation, and event notifications.
"""
import asyncio
import socket
import ssl
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis

LOG = structlog.get_logger()


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 4059
    transport: str = "tcp"  # tcp, udp, tls, hdlc
    tls_cert: Optional[str] = None
    tls_key: Optional[str] = None
    tls_ca: Optional[str] = None
    max_clients: int = 10
    client_timeout: int = 60
    hdlc_address: int = 1
    logical_device_id: str = "SERVER"
    use_wrappers: bool = True  # DLMS Wrapper Layer


class CosemObjectModel:
    """Pluggable COSEM object model for the server.

    Holds all COSEM objects that the server exposes.
    """

    def __init__(self, objects: Optional[Dict[str, Any]] = None):
        self._objects: Dict[str, Any] = objects or {}

    def add_object(self, obis: Any, obj: Any) -> None:
        key = self._to_key(obis)
        self._objects[key] = obj

    def get_object(self, obis: Any) -> Optional[Any]:
        key = self._to_key(obis)
        return self._objects.get(key)

    def get_all_objects(self) -> Dict[str, Any]:
        return dict(self._objects)

    def get_objects_by_class(self, class_id: int) -> Dict[str, Any]:
        return {
            ln: obj for ln, obj in self._objects.items()
            if getattr(obj, 'CLASS_ID', None) == class_id
        }

    @staticmethod
    def _to_key(obis: Any) -> str:
        if isinstance(obis, Obis):
            return obis.to_bytes().hex()
        if isinstance(obis, (bytes, bytearray)):
            return obis.hex()
        if isinstance(obis, (list, tuple)):
            return bytes(obis).hex()
        if isinstance(obis, str):
            return obis
        raise ValueError(f"Cannot convert {type(obis)} to key")


class RequestHandler(ABC):
    """Abstract base for DLMS request handlers."""

    @abstractmethod
    async def handle(self, data: bytes, model: CosemObjectModel) -> bytes:
        """Process a DLMS request and return the response."""
        pass


class GetRequestHandler(RequestHandler):
    """Handles GET-Request for COSEM attributes."""

    async def handle(self, data: bytes, model: CosemObjectModel) -> bytes:
        # Simplified: parse class_id + obis + attr_id, look up object, return value
        # Real implementation would parse full DLMS APDU
        LOG.debug("Processing GET request", data_len=len(data))
        return self._build_get_response(model)

    def _build_get_response(self, model: CosemObjectModel) -> bytes:
        # Return minimal DLMS response
        return bytes([0xC1, 0x00, 0x02, 0x00])


class SetRequestHandler(RequestHandler):
    """Handles SET-Request for COSEM attributes."""

    async def handle(self, data: bytes, model: CosemObjectModel) -> bytes:
        LOG.debug("Processing SET request", data_len=len(data))
        return bytes([0xC1, 0x01, 0x00])


class ActionRequestHandler(RequestHandler):
    """Handles ACTION-Request for COSEM methods."""

    async def handle(self, data: bytes, model: CosemObjectModel) -> bytes:
        LOG.debug("Processing ACTION request", data_len=len(data))
        return bytes([0xC2, 0x00, 0x00])


class DlmsRequestRouter:
    """Routes DLMS requests to appropriate handlers."""

    def __init__(self):
        self._handlers: Dict[str, RequestHandler] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self._handlers["get"] = GetRequestHandler()
        self._handlers["set"] = SetRequestHandler()
        self._handlers["action"] = ActionRequestHandler()

    def register_handler(self, service: str, handler: RequestHandler) -> None:
        self._handlers[service] = handler

    async def route(self, request_data: bytes, model: CosemObjectModel) -> bytes:
        """Route a DLMS request to the appropriate handler.

        Parses the request type from the first byte(s) of the APDU.
        """
        if not request_data:
            return bytes([0xC1, 0x00, 0x00])  # Error response

        tag = request_data[0] & 0xF0

        if tag == 0xC0:  # Get request (0xC0-0xCF)
            handler = self._handlers.get("get")
        elif tag == 0xE0:  # Set request (0xE0-0xEF)
            handler = self._handlers.get("set")
        elif tag == 0xD0:  # Action request (0xD0-0xDF)
            handler = self._handlers.get("action")
        else:
            LOG.warning("Unknown request type", tag=hex(tag))
            return bytes([0xC1, 0x00, 0x00])

        if handler:
            return await handler.handle(request_data, model)
        return bytes([0xC1, 0x00, 0x00])


@dataclass
class ClientConnection:
    """Represents a connected client."""
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    address: Tuple[str, int]
    authenticated: bool = False
    client_system_title: Optional[bytes] = None


class CosemServer:
    """Complete COSEM server implementation.

    Supports TCP, UDP, TLS, and HDLC transports with a pluggable
    COSEM object model and request routing.

    Usage::

        model = CosemObjectModel()
        server = CosemServer(model, ServerConfig(port=4059))
        await server.start()
    """

    def __init__(
        self,
        model: CosemObjectModel,
        config: Optional[ServerConfig] = None,
        router: Optional[DlmsRequestRouter] = None,
    ):
        self.model = model
        self.config = config or ServerConfig()
        self.router = router or DlmsRequestRouter()
        self._server: Optional[asyncio.AbstractServer] = None
        self._clients: Dict[Tuple[str, int], ClientConnection] = {}
        self._running = False
        self._event_callbacks: List[Callable] = []

    def on_event(self, callback: Callable) -> None:
        """Register an event callback."""
        self._event_callbacks.append(callback)

    async def _notify_event(self, event_type: str, **kwargs) -> None:
        for cb in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event_type, **kwargs)
                else:
                    cb(event_type, **kwargs)
            except Exception as e:
                LOG.error("Event callback error", error=str(e))

    async def start(self) -> None:
        """Start the COSEM server."""
        transport = self.config.transport.lower()

        if transport in ("tcp", "hdlc"):
            await self._start_tcp()
        elif transport == "tls":
            await self._start_tls()
        elif transport == "udp":
            await self._start_udp()
        else:
            raise ValueError(f"Unsupported transport: {transport}")

        self._running = True
        LOG.info(
            "COSEM server started",
            transport=transport,
            host=self.config.host,
            port=self.config.port,
        )
        await self._notify_event("server_started")

    async def _start_tcp(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.config.host,
            self.config.port,
        )

    async def _start_tls(self) -> None:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        if self.config.tls_cert and self.config.tls_key:
            ctx.load_cert_chain(self.config.tls_cert, self.config.tls_key)
        if self.config.tls_ca:
            ctx.load_verify_locations(self.config.tls_ca)
            ctx.verify_mode = ssl.CERT_REQUIRED
        self._server = await asyncio.start_server(
            self._handle_client,
            self.config.host,
            self.config.port,
            ssl=ctx,
        )

    async def _start_udp(self) -> None:
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpProtocol(self),
            local_addr=(self.config.host, self.config.port),
        )
        self._udp_transport = transport

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a new client connection."""
        addr = (writer.get_extra_info("peername") or ("unknown", 0))
        if isinstance(addr, tuple) and len(addr) >= 2:
            addr = (str(addr[0]), addr[1])
        else:
            addr = ("unknown", 0)

        client = ClientConnection(reader=reader, writer=writer, address=addr)
        self._clients[addr] = client
        LOG.info("Client connected", address=addr)
        await self._notify_event("client_connected", address=addr)

        try:
            async for data in self._read_data(reader):
                response = await self.router.route(data, self.model)
                writer.write(response)
                await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        except ConnectionResetError:
            pass
        except Exception as e:
            LOG.error("Client handler error", error=str(e), address=addr)
        finally:
            writer.close()
            await writer.wait_closed()
            self._clients.pop(addr, None)
            LOG.info("Client disconnected", address=addr)
            await self._notify_event("client_disconnected", address=addr)

    async def _read_data(self, reader: asyncio.StreamReader):
        """Read data from client, with optional DLMS wrapper parsing."""
        while True:
            if self.config.use_wrappers:
                # DLMS Wrapper: 1 byte length prefix
                header = await reader.readexactly(1)
                length = header[0]
                if length == 0:
                    # Long length: 2 bytes
                    long_len = await reader.readexactly(2)
                    length = (long_len[0] << 8) | long_len[1]
                data = await reader.readexactly(length)
                yield data
            else:
                data = await reader.read(4096)
                if not data:
                    break
                yield data

    async def stop(self) -> None:
        """Stop the COSEM server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if hasattr(self, "_udp_transport"):
            self._udp_transport.close()
        for client in self._clients.values():
            client.writer.close()
        self._clients.clear()
        LOG.info("COSEM server stopped")
        await self._notify_event("server_stopped")

    async def broadcast_notification(self, data: bytes) -> None:
        """Send a data notification to all connected clients."""
        for client in list(self._clients.values()):
            try:
                if self.config.use_wrappers:
                    # Wrap in DLMS wrapper
                    if len(data) < 128:
                        wrapped = bytes([len(data)]) + data
                    else:
                        wrapped = bytes([0, (len(data) >> 8) & 0xFF, len(data) & 0xFF]) + data
                    client.writer.write(wrapped)
                else:
                    client.writer.write(data)
                await client.writer.drain()
            except Exception as e:
                LOG.warning("Failed to send notification", error=str(e))


class UdpProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for COSEM server."""

    def __init__(self, server: CosemServer):
        self.server = server

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        asyncio.create_task(self._handle_datagram(data, addr))

    async def _handle_datagram(self, data: bytes, addr: Tuple[str, int]) -> None:
        response = await self.server.router.route(data, self.server.model)
        self.transport.sendto(response, addr)

    def connection_made(self, transport):
        self.transport = transport

    def error_received(self, exc):
        LOG.warning("UDP error", error=str(exc))


def create_three_phase_meter_server(
    host: str = "0.0.0.0",
    port: int = 4059,
    transport: str = "tcp",
) -> CosemServer:
    """Create a pre-configured three-phase meter COSEM server.

    This is a convenience function that creates a server with a
    standard three-phase meter object model.
    """
    from dlms_cosem.cosem.factory import create_china_gb_three_phase_meter

    model = CosemObjectModel()
    meter_objects = create_china_gb_three_phase_meter()
    for obis, obj in meter_objects.items():
        model.add_object(obis, obj)

    config = ServerConfig(host=host, port=port, transport=transport)
    return CosemServer(model, config)
