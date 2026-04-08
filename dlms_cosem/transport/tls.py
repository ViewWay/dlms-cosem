"""TLS transport layer for DLMS/COSEM over TCP/TLS (Wrapper Layer)."""
from __future__ import annotations

import hashlib
import os
import ssl
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List, Tuple

import structlog

from dlms_cosem.io import IoImplementation
from dlms_cosem.protocol.wrappers import WrapperHeader, WrapperProtocolDataUnit

LOG = structlog.get_logger()


class TLSVersion(IntEnum):
    TLS_1_2 = 0x0303
    TLS_1_3 = 0x0304


class TLSAuthMode(IntEnum):
    NONE = 0
    SERVER_ONLY = 1
    MUTUAL = 2  # mTLS


@dataclass
class TLSCertificateConfig:
    """Certificate configuration for TLS connections."""
    ca_cert_path: Optional[str] = None
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None
    client_key_password: Optional[str] = None
    ca_cert_data: Optional[bytes] = None
    client_cert_data: Optional[bytes] = None
    client_key_data: Optional[bytes] = None


@dataclass
class TLSConfig:
    """Configuration for DLMS over TCP/TLS transport."""
    host: str = "localhost"
    port: int = 4059
    tls_version: TLSVersion = TLSVersion.TLS_1_2
    auth_mode: TLSAuthMode = TLSAuthMode.SERVER_ONLY
    cert_config: Optional[TLSCertificateConfig] = None
    timeout: float = 10.0
    source_address: Optional[Tuple[str, int]] = None
    cipher_suites: Optional[List[str]] = None
    check_hostname: bool = True
    client_logical_address: int = 16
    server_logical_address: int = 1
    max_wrapper_size: int = 2048


@dataclass
class TLSPoolConfig:
    """Connection pool configuration."""
    min_connections: int = 1
    max_connections: int = 10
    idle_timeout: float = 300.0
    connect_timeout: float = 10.0
    max_reuse_count: int = 1000


class TLSError(Exception):
    """TLS transport error."""
    pass


class TLSCertificateError(TLSError):
    """Certificate-related error."""
    pass


class TLSConnectionError(TLSError):
    """Connection error."""
    pass


class CertificateManager:
    """Manages TLS certificates (PEM/DER loading, validation)."""

    @staticmethod
    def load_certificate(path: str) -> bytes:
        """Load a certificate from file."""
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def load_private_key(path: str, password: Optional[str] = None) -> bytes:
        """Load a private key from file."""
        data = CertificateManager.load_certificate(path)
        if password:
            # Password handling is done by ssl module
            pass
        return data

    @staticmethod
    def pem_to_der(pem_data: bytes) -> bytes:
        """Convert PEM to DER format."""
        lines = pem_data.decode("ascii", errors="ignore").strip().split("\n")
        b64 = "".join(
            line.strip() for line in lines
            if not line.startswith("-----")
        )
        import base64
        return base64.b64decode(b64)

    @staticmethod
    def der_to_pem(der_data: bytes, label: str = "CERTIFICATE") -> bytes:
        """Convert DER to PEM format."""
        import base64
        b64 = base64.b64encode(der_data).decode("ascii")
        lines = [f"-----BEGIN {label}-----"]
        for i in range(0, len(b64), 64):
            lines.append(b64[i:i + 64])
        lines.append(f"-----END {label}-----")
        return "\n".join(lines).encode("ascii")

    @staticmethod
    def get_fingerprint(data: bytes, algorithm: str = "sha256") -> str:
        """Get certificate fingerprint."""
        h = hashlib.new(algorithm)
        h.update(data)
        return ":".join(f"{b:02X}" for b in h.digest())

    @staticmethod
    def save_temp_cert(data: bytes, suffix: str = ".pem") -> str:
        """Save certificate data to a temp file and return the path."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        return path


class TLSConnection(IoImplementation):
    """A single TLS connection for DLMS/COSEM."""

    def __init__(self, config: TLSConfig):
        self.config = config
        self._socket: Optional[ssl.SSLSocket] = None
        self._connected = False
        self._reuse_count = 0

    @property
    def connected(self) -> bool:
        return self._connected

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context based on configuration."""
        if self.config.tls_version == TLSVersion.TLS_1_3:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            ctx.maximum_version = ssl.TLSVersion.TLSv1_3

        ctx.check_hostname = self.config.check_hostname

        cert_cfg = self.config.cert_config
        if cert_cfg:
            if cert_cfg.ca_cert_path:
                ctx.load_verify_locations(cert_cfg.ca_cert_path)
            elif cert_cfg.ca_cert_data:
                path = CertificateManager.save_temp_cert(cert_cfg.ca_cert_data)
                try:
                    ctx.load_verify_locations(path)
                finally:
                    os.unlink(path)

            if self.config.auth_mode == TLSAuthMode.MUTUAL:
                if cert_cfg.client_cert_path and cert_cfg.client_key_path:
                    ctx.load_cert_chain(
                        certfile=cert_cfg.client_cert_path,
                        keyfile=cert_cfg.client_key_path,
                        password=cert_cfg.client_key_password,
                    )
                elif cert_cfg.client_cert_data and cert_cfg.client_key_data:
                    cert_path = CertificateManager.save_temp_cert(
                        cert_cfg.client_cert_data, ".pem"
                    )
                    key_path = CertificateManager.save_temp_cert(
                        cert_cfg.client_key_data, ".key"
                    )
                    try:
                        ctx.load_cert_chain(
                            certfile=cert_path,
                            keyfile=key_path,
                            password=cert_cfg.client_key_password,
                        )
                    finally:
                        os.unlink(cert_path)
                        os.unlink(key_path)
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        if self.config.cipher_suites:
            ctx.set_ciphers(":".join(self.config.cipher_suites))

        return ctx

    def connect(self) -> None:
        """Establish TLS connection."""
        if self._connected:
            return

        ctx = self._create_ssl_context()
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(self.config.timeout)

        if self.config.source_address:
            raw_sock.bind(self.config.source_address)

        try:
            raw_sock.connect((self.config.host, self.config.port))
            self._socket = ctx.wrap_socket(
                raw_sock, server_hostname=self.config.host
            )
            self._connected = True
            self._reuse_count = 0
            LOG.info(
                "tls_connected",
                host=self.config.host,
                port=self.config.port,
                version=self._socket.version(),
                cipher=self._socket.cipher(),
            )
        except ssl.SSLError as e:
            raw_sock.close()
            raise TLSCertificateError(f"TLS handshake failed: {e}")
        except socket.timeout:
            raw_sock.close()
            raise TLSConnectionError(
                f"Connection timeout to {self.config.host}:{self.config.port}"
            )
        except OSError as e:
            raw_sock.close()
            raise TLSConnectionError(f"Connection failed: {e}")

    def disconnect(self) -> None:
        """Close TLS connection."""
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None
        self._connected = False

    def send(self, data: bytes) -> None:
        """Send data over TLS."""
        if not self._connected or not self._socket:
            raise TLSConnectionError("Not connected")
        try:
            # Wrap in DLMS Wrapper Layer if not already wrapped
            self._socket.sendall(data)
        except ssl.SSLError as e:
            self._connected = False
            raise TLSError(f"Send failed: {e}")

    def recv(self, amount: int) -> bytes:
        """Receive data over TLS."""
        if not self._connected or not self._socket:
            raise TLSConnectionError("Not connected")
        try:
            return self._socket.recv(amount)
        except ssl.SSLError as e:
            self._connected = False
            raise TLSError(f"Receive failed: {e}")

    def recv_until(self, end: bytes) -> bytes:
        """Receive data until end marker."""
        data = b""
        while not data.endswith(end):
            chunk = self.recv(1)
            if not chunk:
                break
            data += chunk
        return data

    def get_peer_certificate(self) -> Optional[dict]:
        """Get peer certificate info."""
        if not self._socket:
            return None
        cert = self._socket.getpeercert(binary_form=True)
        if cert is None:
            return None
        return {
            "fingerprint_sha256": CertificateManager.get_fingerprint(cert, "sha256"),
            "fingerprint_sha1": CertificateManager.get_fingerprint(cert, "sha1"),
            "size": len(cert),
        }


class TLSConnectionPool:
    """Connection pool for TLS connections."""

    def __init__(self, config: TLSConfig, pool_config: Optional[TLSPoolConfig] = None):
        self.config = config
        self.pool_config = pool_config or TLSPoolConfig()
        self._pool: List[TLSConnection] = []
        self._in_use: List[TLSConnection] = []
        self._lock = threading.Lock()

    def acquire(self) -> TLSConnection:
        """Get a connection from the pool."""
        with self._lock:
            # Try to reuse an idle connection
            while self._pool:
                conn = self._pool.pop(0)
                if conn.connected and conn._reuse_count < self.pool_config.max_reuse_count:
                    conn._reuse_count += 1
                    self._in_use.append(conn)
                    return conn
                else:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass

            # Create new if under limit
            total = len(self._pool) + len(self._in_use)
            if total < self.pool_config.max_connections:
                conn = TLSConnection(self.config)
                self._in_use.append(conn)
                return conn

            raise TLSError("Connection pool exhausted")

    def release(self, conn: TLSConnection) -> None:
        """Return a connection to the pool."""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                if conn.connected and len(self._pool) < self.pool_config.max_connections:
                    self._pool.append(conn)
                else:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass

    def close_all(self) -> None:
        """Close all connections."""
        with self._lock:
            for conn in self._pool + self._in_use:
                try:
                    conn.disconnect()
                except Exception:
                    pass
            self._pool.clear()
            self._in_use.clear()

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "idle": len(self._pool),
                "in_use": len(self._in_use),
            }


class TLSWrapperTransport:
    """DLMS over TCP/TLS using the Wrapper Layer (4-layer model).

    Wrapper Layer adds source/destination addresses and length prefix
    to XDlmsApdu data for TCP/TLS transport.
    """

    def __init__(self, config: TLSConfig):
        self.config = config
        self._connection = TLSConnection(config)
        self.client_logical_address = config.client_logical_address
        self.server_logical_address = config.server_logical_address

    def connect(self) -> None:
        self._connection.connect()

    def disconnect(self) -> None:
        self._connection.disconnect()

    def send(self, data: bytes) -> None:
        """Wrap data in DLMS Wrapper and send."""
        length = len(data) + 4  # length field itself (2 bytes) + padding
        header = struct.pack(">H", length) + b"\x00\x00"
        wrapped = header + data
        self._connection.send(wrapped)

    def receive(self) -> bytes:
        """Receive and unwrap DLMS Wrapper."""
        # Read wrapper header (at least 8 bytes)
        header = self._connection.recv(8)
        if len(header) < 8:
            raise TLSConnectionError("Incomplete wrapper header")

        # Parse length (5th and 6th bytes, big-endian)
        length = struct.unpack(">H", header[4:6])[0]
        # Remaining bytes in wrapper minus already read
        remaining = length - 4  # -4 for the length field itself
        payload = self._connection.recv(remaining)
        return payload

    @property
    def connection(self) -> TLSConnection:
        return self._connection
