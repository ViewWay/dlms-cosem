"""Tests for COSEM Server."""
import asyncio
import pytest
from dlms_cosem.server import (
    CosemServer, CosemObjectModel, ServerConfig,
    DlmsRequestRouter, GetRequestHandler, SetRequestHandler,
    ActionRequestHandler,
)
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C2_Register import Register


def _k(a, b, c, d, e, f):
    return Obis(a, b, c, d, e, f).to_bytes().hex()


class TestCosemObjectModel:
    def test_add_and_get(self):
        model = CosemObjectModel()
        obis = Obis(1, 0, 1, 8, 0, 255)
        reg = Register(obis, value=100)
        model.add_object(obis, reg)
        assert model.get_object(obis) is reg

    def test_add_from_bytes(self):
        model = CosemObjectModel()
        obis_bytes = b'\x01\x00\x01\x08\x00\xff'
        reg = Register(Obis.from_bytes(obis_bytes), value=50)
        model.add_object(obis_bytes, reg)
        result = model.get_object(obis_bytes)
        assert result.value == 50

    def test_get_missing(self):
        model = CosemObjectModel()
        assert model.get_object(Obis(9, 9, 9, 9, 9, 9)) is None

    def test_get_all(self):
        model = CosemObjectModel()
        o1 = Obis(1, 0, 1, 8, 0, 255)
        o2 = Obis(1, 0, 2, 8, 0, 255)
        model.add_object(o1, Register(o1))
        model.add_object(o2, Register(o2))
        assert len(model.get_all_objects()) == 2

    def test_get_by_class(self):
        model = CosemObjectModel()
        obis = Obis(1, 0, 1, 8, 0, 255)
        model.add_object(obis, Register(obis))
        result = model.get_objects_by_class(3)
        assert len(result) == 1


class TestRequestHandlers:
    @pytest.mark.asyncio
    async def test_get_handler(self):
        model = CosemObjectModel()
        handler = GetRequestHandler()
        response = await handler.handle(b'\xC0\x01\x00\x01\x08\x00\xFF\x02', model)
        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_set_handler(self):
        model = CosemObjectModel()
        handler = SetRequestHandler()
        response = await handler.handle(b'\xE0\x01\x00', model)
        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_action_handler(self):
        model = CosemObjectModel()
        handler = ActionRequestHandler()
        response = await handler.handle(b'\xD0\x01\x00', model)
        assert isinstance(response, bytes)


class TestDlmsRequestRouter:
    @pytest.mark.asyncio
    async def test_route_get(self):
        router = DlmsRequestRouter()
        model = CosemObjectModel()
        response = await router.route(b'\xC0\x01\x00', model)
        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_route_set(self):
        router = DlmsRequestRouter()
        model = CosemObjectModel()
        response = await router.route(b'\xE0\x01\x00', model)
        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_route_action(self):
        router = DlmsRequestRouter()
        model = CosemObjectModel()
        response = await router.route(b'\xD0\x01\x00', model)
        assert isinstance(response, bytes)

    @pytest.mark.asyncio
    async def test_route_empty(self):
        router = DlmsRequestRouter()
        model = CosemObjectModel()
        response = await router.route(b'', model)
        assert response[0] == 0xC1


class TestCosemServer:
    def test_create_server(self):
        model = CosemObjectModel()
        config = ServerConfig(port=9999)
        server = CosemServer(model, config)
        assert server.config.port == 9999

    @pytest.mark.asyncio
    async def test_start_stop_tcp(self):
        model = CosemObjectModel()
        config = ServerConfig(port=0)
        server = CosemServer(model, config)
        await server.start()
        assert server._running
        await server.stop()
        assert not server._running

    @pytest.mark.asyncio
    async def test_start_invalid_transport(self):
        model = CosemObjectModel()
        config = ServerConfig(transport="invalid")
        server = CosemServer(model, config)
        with pytest.raises(ValueError):
            await server.start()
