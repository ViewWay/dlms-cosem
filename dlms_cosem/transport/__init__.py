"""Transport layer implementations for DLMS/COSEM."""
from abc import ABC, abstractmethod
from typing import Optional

from dlms_cosem.transport.lorawan import LoRaWANTransport, LoRaConfig, DLMSFragmenter
from dlms_cosem.transport.nbiot import NBIoTTransport, NBConnectConfig, CoAPMessage
from dlms_cosem.transport.tls import (
    TLSConnection, TLSConfig, TLSCertificateConfig,
    TLSConnectionPool, TLSWrapperTransport, TLSVersion,
    TLSAuthMode, CertificateManager, TLSPoolConfig,
    TLSError, TLSCertificateError, TLSConnectionError,
)


class Transport(ABC):
    """Unified transport interface for DLMS/COSEM.

    All transport implementations (TCP, HDLC, TLS, NB-IoT, LoRaWAN, etc.)
    should implement this interface. Both synchronous and asynchronous
    implementations are supported.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish the transport connection."""
        ...

    @abstractmethod
    async def send(self, data: bytes) -> None:
        """Send data over the transport."""
        ...

    @abstractmethod
    async def receive(self) -> bytes:
        """Receive data from the transport. Blocks until data is available."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the transport connection."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the transport is currently connected."""
        ...


class SyncTransportAdapter(Transport):
    """Adapter to wrap synchronous IoImplementation as an async Transport.

    This allows blocking transports (SerialIO, BlockingTcpIO) to be used
    where the async Transport interface is expected.
    """

    def __init__(self, io_impl):
        """
        Args:
            io_impl: A synchronous IoImplementation (connect/disconnect/send/recv).
        """
        self._io = io_impl
        self._connected = False

    async def connect(self) -> None:
        self._io.connect()
        self._connected = True

    async def send(self, data: bytes) -> None:
        self._io.send(data)

    async def receive(self) -> bytes:
        # Note: recv requires an amount parameter for IoImplementation.
        # We read one byte at a time until no more data is available.
        import asyncio
        loop = asyncio.get_event_loop()
        chunks = []
        while True:
            try:
                chunk = await loop.run_in_executor(None, self._io.recv, 4096)
                if not chunk:
                    break
                chunks.append(chunk)
                break  # got a chunk, return it
            except Exception:
                break
        return b"".join(chunks) if chunks else b""

    async def close(self) -> None:
        self._io.disconnect()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


__all__ = [
    "Transport",
    "SyncTransportAdapter",
    "NBIoTTransport", "NBConnectConfig", "CoAPMessage",
    "LoRaWANTransport", "LoRaConfig", "DLMSFragmenter",
    "TLSConnection", "TLSConfig", "TLSCertificateConfig",
    "TLSConnectionPool", "TLSWrapperTransport", "TLSVersion",
    "TLSAuthMode", "CertificateManager", "TLSPoolConfig",
    "TLSError", "TLSCertificateError", "TLSConnectionError",
]
