"""
Tests for SecurityProfile module.
"""
import pytest

from dlms_cosem.key_management import SecurityProfile, SECURITY_STRATEGIES
from dlms_cosem.enumerations import AuthenticationMechanism
from dlms_cosem.exceptions import KeyLengthError


class TestSecurityProfile:
    def test_create_minimal_profile(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
        )
        assert profile.name == "test"
        assert profile.suite == 0

    def test_profile_with_hls_gmac(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            authentication_method=AuthenticationMechanism.HLS_GMAC,
            authenticated=True,
            encrypted=True,
        )
        assert profile.authenticated is True
        assert profile.encrypted is True

    def test_validate_profile_checks_key_length(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"short",  # Wrong length
            authentication_key=b"0123456789ABCDEF",
        )
        with pytest.raises(KeyLengthError):
            profile.validate()

    def test_to_dict_conversion(self):
        profile = SecurityProfile(
            name="test",
            suite=0,
            encryption_key=b"0123456789ABCDEF",
            authentication_key=b"0123456789ABCDEF",
            system_title=b"MDMID000",
        )
        data = profile.to_dict()
        assert data["name"] == "test"
        assert data["suite"] == 0
        assert "encryption_key" in data


class TestSecurityStrategies:
    def test_none_strategy(self):
        profile = SECURITY_STRATEGIES["none"]
        assert profile.suite == 0
        assert profile.authenticated is False
        assert profile.encrypted is False

    def test_lls_strategy(self):
        profile = SECURITY_STRATEGIES["lls"]
        assert profile.authentication_method == AuthenticationMechanism.LLS

    def test_hls_gmac_strategy(self):
        profile = SECURITY_STRATEGIES["hls-gmac"]
        assert profile.authentication_method == AuthenticationMechanism.HLS_GMAC
        assert profile.authenticated is True
        assert profile.encrypted is True

    def test_hls_suite2_strategy(self):
        profile = SECURITY_STRATEGIES["hls-suite2"]
        assert profile.suite == 2
