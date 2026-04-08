import socket

import pytest

from dlms_cosem.exceptions import CommunicationError
from dlms_cosem.io import BlockingTcpIO, IPTransport, TcpTransport


class TestBlockingTcpTransport:

    host = "127.0.0.1"
    port = 0  # use OS-assigned port to avoid conflicts
    client_logical_address = 1
    server_logical_address = 1

    def _get_port(self):
        """Get a free port from the OS."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def test_can_connect(self):
        port = self._get_port()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.listen(1)
        try:
            io = BlockingTcpIO(host="127.0.0.1", port=port)
            transport = IPTransport(
                self.client_logical_address, self.server_logical_address, io
            )
            transport.connect()
            assert transport.io.tcp_socket
            transport.disconnect()
        finally:
            server_socket.close()

    def test_connect_on_connected_raises(self):
        port = self._get_port()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.listen(1)
        try:
            io = BlockingTcpIO(host="127.0.0.1", port=port)
            transport = IPTransport(
                self.client_logical_address, self.server_logical_address, io
            )
            transport.connect()
            with pytest.raises(RuntimeError):
                transport.connect()
            transport.disconnect()
        finally:
            server_socket.close()

    def test_cant_connect_raises_communications_error(self):
        port = self._get_port()
        # Don't bind a server — the port is free but nothing listening
        # Use a port that's very unlikely to be in use
        io = BlockingTcpIO(host="127.0.0.1", port=port)
        transport = IPTransport(
            self.client_logical_address, self.server_logical_address, io
        )
        with pytest.raises(CommunicationError):
            transport.connect()

    def test_disconnect(self):
        port = self._get_port()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.listen(1)
        try:
            io = BlockingTcpIO(host="127.0.0.1", port=port)
            transport = IPTransport(
                self.client_logical_address, self.server_logical_address, io
            )
            transport.connect()
            transport.disconnect()
            assert transport.io.tcp_socket is None
        finally:
            server_socket.close()

    def test_disconnect_is_noop_if_disconnected(self):
        port = self._get_port()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.listen(1)
        try:
            io = BlockingTcpIO(host="127.0.0.1", port=port)
            transport = IPTransport(
                self.client_logical_address, self.server_logical_address, io
            )
            transport.connect()
            transport.disconnect()
            transport.disconnect()
            assert transport.io.tcp_socket is None
        finally:
            server_socket.close()


def test_tcp_transport_is_kept_as_alias_for_backwards_compatibility():
    assert TcpTransport is IPTransport
