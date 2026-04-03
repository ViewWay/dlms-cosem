"""Tests for TLS transport layer."""
import os
import ssl
import socket
import struct
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from dlms_cosem.transport.tls import (
    TLSConnection, TLSConfig, TLSCertificateConfig, TLSConnectionPool,
    TLSWrapperTransport, TLSVersion, TLSAuthMode, CertificateManager,
    TLSCertificateError, TLSConnectionError, TLSError, TLSConnection,
    TLSPoolConfig,
)


class TestCertificateManager:
    def test_pem_to_der(self):
        pem = b"-----BEGIN CERTIFICATE-----\nAAEC\n-----END CERTIFICATE-----\n"
        der = CertificateManager.pem_to_der(pem)
        assert isinstance(der, bytes)
        assert len(der) > 0

    def test_der_to_pem(self):
        der = b"\x00\x01\x02"
        pem = CertificateManager.der_to_pem(der)
        assert b"-----BEGIN CERTIFICATE-----" in pem
        assert b"-----END CERTIFICATE-----" in pem

    def test_roundtrip(self):
        der_orig = os.urandom(64)
        pem = CertificateManager.der_to_pem(der_orig)
        der_back = CertificateManager.pem_to_der(pem)
        assert der_orig == der_back

    def test_get_fingerprint(self):
        data = b"test certificate data"
        fp = CertificateManager.get_fingerprint(data, "sha256")
        assert len(fp.split(":")) == 32  # SHA256 = 32 bytes

    def test_get_fingerprint_sha1(self):
        data = b"test"
        fp = CertificateManager.get_fingerprint(data, "sha1")
        assert len(fp.split(":")) == 20


class TestTLSConfig:
    def test_default_config(self):
        cfg = TLSConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 4059
        assert cfg.tls_version == TLSVersion.TLS_1_2
        assert cfg.auth_mode == TLSAuthMode.SERVER_ONLY

    def test_mtls_config(self):
        cfg = TLSConfig(auth_mode=TLSAuthMode.MUTUAL)
        assert cfg.auth_mode == TLSAuthMode.MUTUAL


class TestTLSConnection:
    @patch("dlms_cosem.transport.tls.TLSConnection._create_ssl_context")
    @patch("socket.socket")
    def test_connect_success(self, mock_socket_cls, mock_ctx):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.version.return_value = "TLSv1.2"
        mock_ssl_sock.cipher.return_value = ("AES256", "TLSv1.2", 256)
        mock_ctx.return_value.wrap_socket.return_value = mock_ssl_sock

        cfg = TLSConfig(check_hostname=False)
        conn = TLSConnection(cfg)
        conn.connect()

        assert conn.connected
        mock_sock.connect.assert_called_once_with(("localhost", 4059))

    @patch("dlms_cosem.transport.tls.TLSConnection._create_ssl_context")
    @patch("socket.socket")
    def test_connect_tls_error(self, mock_socket_cls, mock_ctx):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        mock_ctx.return_value.wrap_socket.side_effect = ssl.SSLError("handshake failed")

        cfg = TLSConfig(check_hostname=False)
        conn = TLSConnection(cfg)
        with pytest.raises(TLSCertificateError):
            conn.connect()

    @patch("dlms_cosem.transport.tls.TLSConnection._create_ssl_context")
    @patch("socket.socket")
    def test_connect_timeout(self, mock_socket_cls, mock_ctx):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.timeout("timed out")
        mock_socket_cls.return_value = mock_sock

        cfg = TLSConfig(timeout=1.0, check_hostname=False)
        conn = TLSConnection(cfg)
        with pytest.raises(TLSConnectionError):
            conn.connect()

    def test_send_not_connected(self):
        cfg = TLSConfig()
        conn = TLSConnection(cfg)
        with pytest.raises(TLSConnectionError):
            conn.send(b"data")

    def test_recv_not_connected(self):
        cfg = TLSConfig()
        conn = TLSConnection(cfg)
        with pytest.raises(TLSConnectionError):
            conn.recv(1024)

    def test_disconnect(self):
        conn = TLSConnection(TLSConfig())
        conn._socket = MagicMock()
        conn._connected = True
        conn.disconnect()
        assert not conn.connected
        assert conn._socket is None


class TestTLSConnectionPool:
    def test_acquire_and_release(self):
        cfg = TLSConfig(check_hostname=False)
        pool = TLSConnectionPool(cfg, TLSPoolConfig(max_connections=5))
        conn = pool.acquire()
        assert isinstance(conn, TLSConnection)
        conn._connected = True
        pool.release(conn)
        assert pool.stats["idle"] == 1

    def test_pool_exhausted(self):
        cfg = TLSConfig(check_hostname=False)
        pool = TLSConnectionPool(cfg, TLSPoolConfig(max_connections=1))
        conn1 = pool.acquire()
        with pytest.raises(TLSError, match="exhausted"):
            pool.acquire()
        pool.release(conn1)

    def test_close_all(self):
        cfg = TLSConfig(check_hostname=False)
        pool = TLSConnectionPool(cfg)
        conn = pool.acquire()
        pool.close_all()
        assert pool.stats["idle"] == 0
        assert pool.stats["in_use"] == 0


class TestTLSWrapperTransport:
    def test_send_wraps_data(self):
        cfg = TLSConfig(check_hostname=False)
        transport = TLSWrapperTransport(cfg)
        transport._connection = MagicMock()
        transport.send(b"\xc0\x01\x00")
        assert transport._connection.send.called
        sent = transport._connection.send.call_args[0][0]
        assert len(sent) > 3

    def test_receive_unwraps_data(self):
        cfg = TLSConfig(check_hostname=False)
        transport = TLSWrapperTransport(cfg)
        transport._connection = MagicMock()
        # Simulate 8-byte header with length field
        header = bytes([0xe0, 0x00]) + bytes([0x00, 0x08, 0x00, 0x00, 0x00, 0x00])
        payload = b"\xc0\x01\x00"
        transport._connection.recv.side_effect = [header, payload]
        result = transport.receive()
        assert result == payload


class TestTLSConnectionPoolStats:
    def test_stats_empty(self):
        cfg = TLSConfig(check_hostname=False)
        pool = TLSConnectionPool(cfg)
        stats = pool.stats
        assert stats["idle"] == 0
        assert stats["in_use"] == 0
