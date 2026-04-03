"""Async DLMS/COSEM client based on asyncio."""
from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Any, Callable

import structlog

from dlms_cosem import cosem, enumerations, exceptions
from dlms_cosem.hdlc import connection as hdlc_conn
from dlms_cosem.protocol.wrappers import WrapperHeader
from dlms_cosem.protocol import acse, xdlms

LOG = structlog.get_logger()


class ConnectionState(IntEnum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED_HDLC = 2
    ASSOCIATED = 3


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True


@dataclass
class AsyncClientConfig:
    host: str = "localhost"
    port: int = 4059
    client_logical_address: int = 16
    server_logical_address: int = 1
    timeout: float = 10.0
    retry: RetryConfig = field(default_factory=RetryConfig)
    use_wrapper: bool = False


class AsyncHDLCConnection:
    """Async HDLC connection over TCP."""

    def __init__(self, config: AsyncClientConfig):
        self.config = config
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.config.host, self.config.port),
            timeout=self.config.timeout,
        )
        self._connected = True

    async def disconnect(self) -> None:
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._connected = False
        self._reader = None
        self._writer = None

    async def send(self, data: bytes) -> None:
        if not self._writer:
            raise exceptions.ConnectionError("Not connected")
        self._writer.write(data)
        await self._writer.drain()

    async def recv(self, amount: int) -> bytes:
        if not self._reader:
            raise exceptions.ConnectionError("Not connected")
        return await asyncio.wait_for(
            self._reader.read(amount), timeout=self.config.timeout
        )

    async def recv_until(self, end: bytes) -> bytes:
        if not self._reader:
            raise exceptions.ConnectionError("Not connected")
        data = b""
        while not data.endswith(end):
            chunk = await asyncio.wait_for(
                self._reader.read(1), timeout=self.config.timeout
            )
            if not chunk:
                break
            data += chunk
        return data


class AsyncDlmsClient:
    """Async DLMS/COSEM client for reading/writing meter data."""

    def __init__(self, config: Optional[AsyncClientConfig] = None):
        self.config = config or AsyncClientConfig()
        self._hdlc = AsyncHDLCConnection(self.config)
        self._state = ConnectionState.DISCONNECTED
        self._association: Optional[acse.ApplicationAssociationResponse] = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    async def connect(self) -> None:
        """Connect to the meter (HDLC level)."""
        self._state = ConnectionState.CONNECTING
        try:
            await self._hdlc.connect()
            self._state = ConnectionState.CONNECTED_HDLC
            LOG.info("async_hdlc_connected", host=self.config.host, port=self.config.port)
        except (asyncio.TimeoutError, OSError) as e:
            self._state = ConnectionState.DISCONNECTED
            raise exceptions.ConnectionError(f"HDLC connect failed: {e}")

    async def associate(
        self,
        authentication: Optional[Any] = None,
        password: Optional[bytes] = None,
    ) -> acse.ApplicationAssociationResponse:
        """Perform AA (Application Association)."""
        if self._state < ConnectionState.CONNECTED_HDLC:
            await self.connect()

        aarq = acse.ApplicationAssociationRequest(
            system_title=b"ASYNC",
            authentication_value=password,
        )
        data = aarq.to_bytes()

        await self._send_with_retry(data)
        response_data = await self._hdlc.recv_until(b"\x7e")

        # Strip HDLC framing
        response_data = self._strip_hdlc(response_data)

        aare = acse.ApplicationAssociationResponse.from_bytes(response_data)
        self._association = aare
        self._state = ConnectionState.ASSOCIATED
        LOG.info("async_associated")
        return aare

    async def get(
        self,
        obis: cosem.Obis,
        attribute: int = 1,
        selector: Optional[int] = None,
    ) -> Any:
        """Get a COSEM attribute value."""
        if self._state < ConnectionState.ASSOCIATED:
            raise exceptions.ConnectionError("Not associated")

        get_req = xdlms.GetRequest(
            cosem_attribute=cosem.CosemAttribute(
                interface=str(obis),
                attribute=attribute,
            ),
        )
        data = get_req.to_bytes()
        await self._send_with_retry(data)
        response_data = await self._hdlc.recv_until(b"\x7e")
        response_data = self._strip_hdlc(response_data)

        get_resp = xdlms.GetResponse.from_bytes(response_data)
        if get_resp.result is not None:
            return get_resp.result
        return None

    async def set(
        self,
        obis: cosem.Obis,
        attribute: int,
        value: Any,
    ) -> Any:
        """Set a COSEM attribute value."""
        if self._state < ConnectionState.ASSOCIATED:
            raise exceptions.ConnectionError("Not associated")

        set_req = xdlms.SetRequest(
            cosem_attribute=cosem.CosemAttribute(
                interface=str(obis),
                attribute=attribute,
            ),
            value=value,
        )
        data = set_req.to_bytes()
        await self._send_with_retry(data)
        response_data = await self._hdlc.recv_until(b"\x7e")
        response_data = self._strip_hdlc(response_data)

        return xdlms.SetResponse.from_bytes(response_data)

    async def action(
        self,
        obis: cosem.Obis,
        method: int,
        *args,
    ) -> Any:
        """Invoke a COSEM method."""
        if self._state < ConnectionState.ASSOCIATED:
            raise exceptions.ConnectionError("Not associated")

        action_req = xdlms.ActionRequest(
            cosem_method=cosem.CosemMethod(
                interface=str(obis),
                method=method,
            ),
        )
        data = action_req.to_bytes()
        await self._send_with_retry(data)
        response_data = await self._hdlc.recv_until(b"\x7e")
        response_data = self._strip_hdlc(response_data)

        return xdlms.ActionResponse.from_bytes(response_data)

    async def disconnect(self) -> None:
        """Disconnect from the meter."""
        if self._state >= ConnectionState.ASSOCIATED and self._hdlc.connected:
            try:
                rlrq = acse.ReleaseRequest()
                await self._hdlc.send(rlrq.to_bytes())
            except Exception:
                pass
        await self._hdlc.disconnect()
        self._state = ConnectionState.DISCONNECTED
        self._association = None
        LOG.info("async_disconnected")

    async def _send_with_retry(self, data: bytes) -> None:
        """Send with retry logic."""
        cfg = self.config.retry
        last_error = None
        for attempt in range(cfg.max_retries):
            try:
                await self._hdlc.send(data)
                return
            except (asyncio.TimeoutError, OSError) as e:
                last_error = e
                if attempt < cfg.max_retries - 1:
                    delay = min(cfg.base_delay * (cfg.backoff_factor ** attempt), cfg.max_delay)
                    if cfg.jitter:
                        import random
                        delay *= random.uniform(0.5, 1.5)
                    LOG.warning("async_retry", attempt=attempt, delay=delay)
                    await asyncio.sleep(delay)
        raise exceptions.ConnectionError(f"All retries exhausted: {last_error}")

    @staticmethod
    def _strip_hdlc(data: bytes) -> bytes:
        """Strip HDLC frame markers."""
        data = data.strip(b"\x7e")
        return data

    async def __aenter__(self) -> "AsyncDlmsClient":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.disconnect()
