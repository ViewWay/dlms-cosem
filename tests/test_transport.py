"""Tests for NB-IoT and LoRaWAN transport layers."""
import pytest

from dlms_cosem.transport.nbiot import (
    NBIoTTransport, NBConnectConfig, CoAPMessage,
    CoAPMessageType, CoAPResponseCode,
)
from dlms_cosem.transport.lorawan import (
    LoRaWANTransport, LoRaConfig, DLMSFragmenter,
    LoRaWANClass, LoRaBand,
)


class TestCoAPMessage:
    def test_encode_decode(self):
        msg = CoAPMessage(
            msg_type=CoAPMessageType.CON,
            code=2,  # POST
            msg_id=42,
            token=b"\x01\x02",
            payload=b"hello",
        )
        data = msg.to_bytes()
        parsed = CoAPMessage.from_bytes(data)
        assert parsed.code == 2
        assert parsed.msg_id == 42
        assert parsed.token == b"\x01\x02"
        assert parsed.payload == b"hello"
        assert parsed.msg_type == CoAPMessageType.CON

    def test_empty_payload(self):
        msg = CoAPMessage(msg_type=CoAPMessageType.ACK, code=68, msg_id=1)
        data = msg.to_bytes()
        parsed = CoAPMessage.from_bytes(data)
        assert parsed.payload == b""


class TestDLMSFragmenter:
    def test_no_fragmentation_needed(self):
        f = DLMSFragmenter(100)
        data = b"\x01\x02\x03"
        fragments = f.fragment(data)
        assert len(fragments) == 1

    def test_fragmentation(self):
        f = DLMSFragmenter(20)  # 20 bytes max, 16 bytes data per fragment
        data = bytes(range(50))  # 50 bytes
        fragments = f.fragment(data)
        assert len(fragments) > 1

    def test_defragment(self):
        f = DLMSFragmenter(20)
        data = bytes(range(50))
        fragments = f.fragment(data)
        result = f.defragment(fragments)
        assert result == data

    def test_defragment_single(self):
        f = DLMSFragmenter(100)
        data = bytes(range(30))
        fragments = f.fragment(data)
        assert len(fragments) == 1
        result = f.defragment(fragments)
        assert result == data


class TestNBIoTTransport:
    def test_create(self):
        config = NBConnectConfig(host="10.0.0.1", port=5683, plmn="46000")
        assert config.plmn == "46000"

    def test_context_manager(self):
        t = NBIoTTransport(NBConnectConfig(host="127.0.0.1", port=12345, timeout=0.1))
        # Should not raise on connect (UDP)
        t.connect()
        assert t.is_connected
        t.disconnect()
        assert not t.is_connected


class TestLoRaWANTransport:
    def test_create(self):
        config = LoRaConfig(
            dev_eui=b"\x01" * 8,
            lora_class=LoRaWANClass.CLASS_A,
            band=LoRaBand.CN470,
        )
        assert config.band == LoRaBand.CN470

    def test_join(self):
        t = LoRaWANTransport(LoRaConfig())
        t.connect()
        assert t.is_connected
        t.disconnect()

    def test_send_requires_connect(self):
        t = LoRaWANTransport(LoRaConfig())
        with pytest.raises(ConnectionError):
            t.send(b"\x01\x02\x03")
