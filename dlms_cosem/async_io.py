"""Async IO and transport implementations for DLMS/COSEM."""
from __future__ import annotations

import asyncio
from typing import Optional, Tuple

import structlog

from dlms_cosem import exceptions

LOG = structlog.get_logger()


class AsyncTcpIO:
    """Async TCP IO implementation using asyncio streams."""

    def __init__(self, host: str, port: int, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    @property
    def address(self) -> Tuple[str, int]:
        return self.host, self.port

    async def connect(self) -> None:
        if self._writer is not None:
            raise RuntimeError(f"Already connected to {self.address}")
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
        except (OSError, asyncio.TimeoutError) as e:
            raise exceptions.CommunicationError("Unable to connect socket") from e
        LOG.info("Connected", address=self.address)

    async def disconnect(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError as e:
                raise exceptions.CommunicationError(str(e)) from e  # type: ignore[call-arg]
            finally:
                self._writer = None
                self._reader = None
        LOG.info("Connection closed", address=self.address)

    async def send(self, data: bytes) -> None:
        if not self._writer:
            raise RuntimeError("Not connected")
        try:
            self._writer.write(data)
            await self._writer.drain()
        except (OSError, ConnectionError) as e:
            raise exceptions.CommunicationError("Could not send data") from e

    async def recv(self, amount: int = 1) -> bytes:
        if not self._reader:
            raise RuntimeError("Not connected")
        try:
            data = await asyncio.wait_for(self._reader.read(amount), timeout=self.timeout)
            return data
        except asyncio.TimeoutError as e:
            raise exceptions.CommunicationError("Receive timed out") from e
        except (OSError, ConnectionError) as e:
            raise exceptions.CommunicationError("Could not receive data") from e

    async def recv_until(self, end: bytes, max_size: int = 4096) -> bytes:
        """Read until end marker is found."""
        if not self._reader:
            raise RuntimeError("Not connected")
        buffer = bytearray()
        while len(buffer) < max_size:
            try:
                chunk = await asyncio.wait_for(
                    self._reader.read(min(1024, max_size - len(buffer))),
                    timeout=self.timeout,
                )
                if not chunk:
                    break
                buffer.extend(chunk)
                idx = buffer.find(end)
                if idx >= 0:
                    return bytes(buffer[: idx + len(end)])
            except asyncio.TimeoutError:
                continue
        return bytes(buffer)
