"""DLMS 连接安全测试 — 参考 pdlms 分层模式。

覆盖层级：
  1. ACSE 层: AARQ/AARE 建链, RLRQ/RLRE 释放
  2. 安全控制: SecurityControlField, SM4 加解密
  3. 认证机制: NoSecurity, LLS, HLS (GMAC/ISM/Common)
  4. 状态机: 连接生命周期转换
  5. 加密连接: DlmsConnection + encryption key 完整流程
"""

import pytest

import dlms_cosem.enumerations as enums
from dlms_cosem.connection import DlmsConnection
from dlms_cosem.exceptions import LocalDlmsProtocolError
from dlms_cosem.protocol.acse.aarq import ApplicationAssociationRequest
from dlms_cosem.protocol.acse.aare import ApplicationAssociationResponse
from dlms_cosem.protocol.acse.rlrq import ReleaseRequest
from dlms_cosem.protocol.acse.rlre import ReleaseResponse
from dlms_cosem.security import (
    HighLevelSecurityCommonAuthentication,
    HighLevelSecurityGmacAuthentication,
    HighLevelSecurityISMAuthentication,
    LowLevelSecurityAuthentication,
    NoSecurityAuthentication,
    SM4Cipher,
    SecurityControlField,
)
from dlms_cosem.state import (
    AWAITING_ASSOCIATION_RESPONSE,
    AWAITING_RELEASE_RESPONSE,
    NO_ASSOCIATION,
    READY,
    DlmsConnectionState,
)


# ─── Helpers ──────────────────────────────────────────────


def _make_no_sec_conn() -> DlmsConnection:
    return DlmsConnection(
        authentication=NoSecurityAuthentication(),
        client_system_title=b"TESTCLI0",
    )


def _make_enc_conn() -> DlmsConnection:
    """Connection with AES-GCM encryption keys."""
    return DlmsConnection(
        authentication=NoSecurityAuthentication(),
        client_system_title=b"TESTCLI0",
        global_encryption_key=bytes(range(16)),
        global_authentication_key=bytes(range(16)),
        security_suite=0,
    )


# ─── 1. ACSE 层: AARQ/AARE ───────────────────────────────


class TestAARQ:
    """AARQ 序列化与反序列化。"""

    def test_tag_is_0x60(self):
        aarq = _make_no_sec_conn().get_aarq()
        raw = aarq.to_bytes()
        assert raw[0] == 0x60

    def test_roundtrip(self):
        aarq = _make_no_sec_conn().get_aarq()
        raw = aarq.to_bytes()
        aarq2 = ApplicationAssociationRequest.from_bytes(raw)
        assert aarq2.ciphered is False
        assert aarq2.system_title == b"TESTCLI0"

    def test_contains_user_information(self):
        aarq = _make_no_sec_conn().get_aarq()
        assert aarq.user_information is not None

    def test_ciphered_false_by_default(self):
        aarq = _make_no_sec_conn().get_aarq()
        assert aarq.ciphered is False

    def test_system_title_preserved(self):
        conn = DlmsConnection(
            authentication=NoSecurityAuthentication(),
            client_system_title=b"SYS12345",
        )
        aarq = conn.get_aarq()
        raw = aarq.to_bytes()
        aarq2 = ApplicationAssociationRequest.from_bytes(raw)
        assert aarq2.system_title == b"SYS12345"


class TestAARE:
    """AARE 序列化与反序列化。"""

    def test_tag_is_0x61(self):
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.ACCEPTED,
            result_source_diagnostics=enums.AcseServiceUserDiagnostics.NULL,
        )
        raw = aare.to_bytes()
        assert raw[0] == 0x61

    def test_accepted_roundtrip(self):
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.ACCEPTED,
            result_source_diagnostics=enums.AcseServiceUserDiagnostics.NULL,
        )
        raw = aare.to_bytes()
        aare2 = ApplicationAssociationResponse.from_bytes(raw)
        assert aare2.result == enums.AssociationResult.ACCEPTED

    def test_rejected(self):
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.REJECTED_PERMANENT,
            result_source_diagnostics=enums.AcseServiceUserDiagnostics.NO_REASON_GIVEN,
        )
        raw = aare.to_bytes()
        aare2 = ApplicationAssociationResponse.from_bytes(raw)
        assert aare2.result == enums.AssociationResult.REJECTED_PERMANENT


# ─── 2. ACSE 层: RLRQ/RLRE ──────────────────────────────


class TestRLRQ:
    """RLRQ 序列化与反序列化。"""

    def test_tag_is_0x62(self):
        rlrq = _make_no_sec_conn().get_rlrq()
        raw = rlrq.to_bytes()
        assert raw[0] == 0x62

    def test_roundtrip(self):
        rlrq = _make_no_sec_conn().get_rlrq()
        raw = rlrq.to_bytes()
        rlrq2 = ReleaseRequest.from_bytes(raw)
        assert isinstance(rlrq2, ReleaseRequest)


class TestRLRE:
    """RLRE 序列化与反序列化。"""

    def test_tag_is_0x63(self):
        rlre = ReleaseResponse(reason=enums.ReleaseResponseReason.NORMAL)
        raw = rlre.to_bytes()
        assert raw[0] == 0x63

    def test_roundtrip(self):
        rlre = ReleaseResponse(reason=enums.ReleaseResponseReason.NORMAL)
        raw = rlre.to_bytes()
        rlre2 = ReleaseResponse.from_bytes(raw)
        assert rlre2.reason == enums.ReleaseResponseReason.NORMAL


# ─── 3. SecurityControlField ─────────────────────────────


class TestSecurityControlField:
    def test_no_security(self):
        sc = SecurityControlField(security_suite=0)
        assert sc.authenticated is False
        assert sc.encrypted is False

    def test_authenticated_only(self):
        sc = SecurityControlField(security_suite=0, authenticated=True)
        assert sc.authenticated is True
        assert sc.encrypted is False

    def test_encrypted_only(self):
        sc = SecurityControlField(security_suite=0, encrypted=True)
        assert sc.authenticated is False
        assert sc.encrypted is True

    def test_authenticated_and_encrypted(self):
        sc = SecurityControlField(
            security_suite=1, authenticated=True, encrypted=True
        )
        raw = sc.to_bytes()
        sc2 = SecurityControlField.from_bytes(raw)
        assert sc2.security_suite == 1
        assert sc2.authenticated is True
        assert sc2.encrypted is True

    def test_roundtrip_all_suites(self):
        for suite in range(5):
            for auth in (True, False):
                for enc in (True, False):
                    sc = SecurityControlField(
                        security_suite=suite, authenticated=auth, encrypted=enc
                    )
                    raw = sc.to_bytes()
                    sc2 = SecurityControlField.from_bytes(raw)
                    assert sc2.security_suite == suite
                    assert sc2.authenticated == auth
                    assert sc2.encrypted == enc


# ─── 4. SM4 加解密 ───────────────────────────────────────


class TestSM4Cipher:
    def test_roundtrip_short(self):
        c = SM4Cipher(key=bytes(16))
        pt = b"Hello!"
        assert c.decrypt(c.encrypt(pt)) == pt

    def test_roundtrip_1kb(self):
        c = SM4Cipher(key=bytes(16))
        pt = bytes(range(256)) * 4
        assert c.decrypt(c.encrypt(pt)) == pt

    def test_different_keys_different_ciphertext(self):
        c1 = SM4Cipher(key=bytes(16))
        c2 = SM4Cipher(key=bytes([i ^ 0xFF for i in range(16)]))
        pt = b"test data here!!"  # 16 bytes
        assert c1.encrypt(pt) != c2.encrypt(pt)

    def test_same_key_deterministic(self):
        c = SM4Cipher(key=bytes(16))
        pt = b"deterministic!!!"
        assert c.encrypt(pt) == c.encrypt(pt)


# ─── 5. 认证机制 ─────────────────────────────────────────


class TestAuthenticationMechanisms:
    def test_no_security(self):
        auth = NoSecurityAuthentication()
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert aarq.ciphered is False

    def test_lls_with_secret(self):
        auth = LowLevelSecurityAuthentication(secret=b"pass1234")
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)

    def test_lls_no_secret(self):
        auth = LowLevelSecurityAuthentication(secret=None)
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)

    def test_hls_gmac(self):
        auth = HighLevelSecurityGmacAuthentication(challenge_length=32)
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)

    def test_hls_ism(self):
        auth = HighLevelSecurityISMAuthentication(secret=b"\x00" * 16, security_suite=0)
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)

    def test_hls_common(self):
        auth = HighLevelSecurityCommonAuthentication(secret=b"\x00" * 16)
        conn = DlmsConnection(authentication=auth, client_system_title=b"TEST")
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)


# ─── 6. 状态机转换 ───────────────────────────────────────


class TestStateMachineTransitions:
    def test_initial_state(self):
        st = DlmsConnectionState()
        assert st.current_state is NO_ASSOCIATION

    def test_aarq_transitions_to_awaiting(self):
        st = DlmsConnectionState()
        aarq = _make_no_sec_conn().get_aarq()
        st.process_event(aarq)
        assert st.current_state is AWAITING_ASSOCIATION_RESPONSE

    def test_aare_accepted_transitions_to_ready(self):
        st = DlmsConnectionState()
        st.process_event(_make_no_sec_conn().get_aarq())
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.ACCEPTED,
            result_source_diagnostics=enums.AcseServiceUserDiagnostics.NULL,
        )
        st.process_event(aare)
        assert st.current_state is READY

    def test_aare_rejected_stays_ready(self):
        """dlms-cosem 状态机: 被拒绝的 AARE 仍然转换到 READY."""
        st = DlmsConnectionState()
        st.process_event(_make_no_sec_conn().get_aarq())
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.REJECTED_PERMANENT,
            result_source_diagnostics=enums.AcseServiceUserDiagnostics.NO_REASON_GIVEN,
        )
        st.process_event(aare)
        # dlms-cosem 不管 accept/reject 都到 READY
        assert st.current_state is READY

    def test_rlrq_from_ready(self):
        st = DlmsConnectionState()
        st.current_state = READY
        rlrq = _make_no_sec_conn().get_rlrq()
        st.process_event(rlrq)
        assert st.current_state is AWAITING_RELEASE_RESPONSE

    def test_rlre_completes_disconnect(self):
        st = DlmsConnectionState()
        st.current_state = AWAITING_RELEASE_RESPONSE
        rlre = ReleaseResponse(reason=enums.ReleaseResponseReason.NORMAL)
        st.process_event(rlre)
        assert st.current_state is NO_ASSOCIATION


# ─── 7. 加密连接完整流程 ────────────────────────────────


class TestEncryptedConnection:
    def test_encrypted_aarq_generation(self):
        conn = _make_enc_conn()
        aarq = conn.get_aarq()
        assert isinstance(aarq, ApplicationAssociationRequest)
        raw = aarq.to_bytes()
        assert len(raw) > 0

    def test_encrypted_rlrq_generation(self):
        conn = _make_enc_conn()
        rlrq = conn.get_rlrq()
        raw = rlrq.to_bytes()
        assert len(raw) > 0

    def test_security_control_with_encryption(self):
        conn = _make_enc_conn()
        sc = conn.security_control
        assert isinstance(sc, SecurityControlField)
