"""Tests for COSEM Factory."""
import pytest
from dlms_cosem.cosem.factory import (
    create_cosem_object,
    create_china_gb_three_phase_meter,
    create_single_phase_meter,
    _get_registry,
)
from dlms_cosem.cosem.obis import Obis
from dlms_cosem import enumerations as enums


class TestCosemFactory:
    def test_create_register(self):
        obj = create_cosem_object(3, b'\x01\x00\x01\x08\x00\xff')
        assert obj.CLASS_ID == 3
        assert isinstance(obj.logical_name, Obis)

    def test_create_register_from_obis(self):
        obis = Obis(1, 0, 1, 8, 0, 255)
        obj = create_cosem_object(3, obis)
        assert obj.logical_name == obis

    def test_create_from_hex_string(self):
        obj = create_cosem_object(3, "0100010800ff")
        assert obj.CLASS_ID == 3

    def test_create_clock(self):
        obj = create_cosem_object(8, (0, 0, 1, 0, 0, 255))
        assert obj.CLASS_ID == enums.CosemInterface.CLOCK

    def test_create_with_extra_kwargs(self):
        obj = create_cosem_object(3, (1, 0, 1, 8, 0, 255), value=100)
        assert obj.value == 100

    def test_unknown_class_id(self):
        obj = create_cosem_object(9999, (1, 0, 1, 8, 0, 255))
        assert obj.CLASS_ID == 9999
        assert hasattr(obj, 'logical_name')

    def test_invalid_logical_name(self):
        with pytest.raises(ValueError):
            create_cosem_object(3, 12345)


class TestRegistry:
    def test_registry_has_known_classes(self):
        reg = _get_registry()
        assert enums.CosemInterface.REGISTER in reg
        assert enums.CosemInterface.CLOCK in reg
        assert enums.CosemInterface.DATA in reg
        assert enums.CosemInterface.PROFILE_GENERIC in reg
        assert enums.CosemInterface.SECURITY_SETUP in reg

    def test_registry_size(self):
        reg = _get_registry()
        assert len(reg) >= 20


class TestChinaGBFactory:
    def test_three_phase_meter(self):
        objects = create_china_gb_three_phase_meter()
        assert len(objects) >= 15
        energy_key = Obis(1, 0, 1, 8, 0, 255).to_bytes().hex()
        assert energy_key in objects
        assert objects[energy_key].value == 12345.67

    def test_three_phase_has_clock(self):
        objects = create_china_gb_three_phase_meter()
        clock_key = Obis(0, 0, 1, 0, 0, 255).to_bytes().hex()
        assert clock_key in objects

    def test_three_phase_has_voltage(self):
        objects = create_china_gb_three_phase_meter()
        assert Obis(1, 0, 32, 7, 0, 255).to_bytes().hex() in objects
        assert Obis(1, 0, 52, 7, 0, 255).to_bytes().hex() in objects
        assert Obis(1, 0, 72, 7, 0, 255).to_bytes().hex() in objects

    def test_single_phase_meter(self):
        objects = create_single_phase_meter()
        assert len(objects) >= 5
        clock_key = Obis(0, 0, 1, 0, 0, 255).to_bytes().hex()
        assert clock_key in objects
