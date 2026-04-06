"""Supplementary tests for COSEM objects."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.register import Register
from dlms_cosem.cosem.data import Data
from dlms_cosem.cosem.clock import Clock
from dlms_cosem.cosem.extended_register import ExtendedRegister
from dlms_cosem.cosem.demand_register import DemandRegister
from dlms_cosem.cosem.profile_generic import ProfileGeneric
from dlms_cosem.cosem.script_table import ScriptTable
from dlms_cosem.cosem.action_schedule import ActionSchedule
from dlms_cosem.cosem.association_sn import AssociationSN
from dlms_cosem.cosem.security_setup import SecuritySetup
from dlms_cosem.cosem.image_transfer import ImageTransfer


class TestRegister:
    def test_creation(self):
        r = Register(Obis(0, 0, 1, 0, 0, 255))
        assert r is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert Register.CLASS_ID == enumerations.CosemInterface.REGISTER


class TestData:
    def test_creation(self):
        d = Data(Obis(0, 0, 96, 10, 0, 255))
        assert d is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert Data.CLASS_ID == enumerations.CosemInterface.DATA


class TestClock:
    def test_creation(self):
        c = Clock(Obis(0, 0, 1, 0, 0, 255))
        assert c is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert Clock.CLASS_ID == enumerations.CosemInterface.CLOCK


class TestExtendedRegister:
    def test_creation(self):
        er = ExtendedRegister(Obis(0, 0, 1, 0, 0, 255))
        assert er is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert ExtendedRegister.CLASS_ID == enumerations.CosemInterface.EXTENDED_REGISTER


class TestDemandRegister:
    def test_creation(self):
        dr = DemandRegister(Obis(0, 0, 1, 0, 0, 255))
        assert dr is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert DemandRegister.CLASS_ID == enumerations.CosemInterface.DEMAND_REGISTER


class TestProfileGeneric:
    def test_creation(self):
        pg = ProfileGeneric(Obis(0, 0, 1, 0, 0, 255))
        assert pg is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert ProfileGeneric.INTERFACE_CLASS_ID == enumerations.CosemInterface.PROFILE_GENERIC


class TestScriptTable:
    def test_creation(self):
        st = ScriptTable(Obis(0, 0, 10, 0, 0, 255))
        assert st is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert ScriptTable.CLASS_ID == enumerations.CosemInterface.SCRIPT_TABLE


class TestActionSchedule:
    def test_creation(self):
        as_ = ActionSchedule(Obis(0, 0, 10, 0, 0, 255))
        assert as_ is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert ActionSchedule.CLASS_ID == enumerations.CosemInterface.SCHEDULE


class TestAssociationSN:
    def test_creation(self):
        asn = AssociationSN(Obis(0, 0, 40, 0, 0, 255))
        assert asn is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert AssociationSN.CLASS_ID == enumerations.CosemInterface.ASSOCIATION_SN


class TestSecuritySetup:
    def test_creation(self):
        ss = SecuritySetup(Obis(0, 0, 43, 0, 0, 255))
        assert ss is not None

    def test_class_id(self):
        from dlms_cosem import enumerations
        assert SecuritySetup.CLASS_ID == enumerations.CosemInterface.SECURITY_SETUP


class TestImageTransfer:
    def test_creation(self):
        it = ImageTransfer(Obis(0, 0, 44, 0, 0, 255))
        assert it is not None

    def test_class_id(self):
        assert ImageTransfer.CLASS_ID == 68


class TestCosemFactory:
    def test_create_register(self):
        from dlms_cosem.cosem.factory import create_cosem_object
        obj = create_cosem_object(3, Obis(0, 0, 1, 0, 0, 255))
        assert obj is not None

    def test_create_data(self):
        from dlms_cosem.cosem.factory import create_cosem_object
        obj = create_cosem_object(1, Obis(0, 0, 96, 10, 0, 255))
        assert obj is not None

    def test_create_unknown_class(self):
        from dlms_cosem.cosem.factory import create_cosem_object
        obj = create_cosem_object(999, Obis(0, 0, 0, 0, 0, 255))
        assert obj is not None
