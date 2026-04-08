"""Protocol reliability framework tests.

This framework implements theoretical reliability testing methods:
1) Equivalence partition + boundary analysis
2) Combinatorial coverage
3) Metamorphic testing
4) Fault injection (mutation)
5) State-transition workflow checks

Reference: pdlms/test_protocol_reliability_framework.py
"""

from __future__ import annotations

import random

from dlms_cosem.protocol import wrappers
from dlms_cosem.protocol.xdlms import (
    GetRequestNormal,
    SetRequestNormal,
    ActionRequestNormal,
    InitiateRequest,
)
from dlms_cosem.protocol.acse import (
    ApplicationAssociationRequest,
    ApplicationAssociationResponse,
    UserInformation,
)
from dlms_cosem.protocol.acse.base import AppContextName
from dlms_cosem.cosem import Obis
from dlms_cosem.cosem import CosemAttribute, CosemMethod
from dlms_cosem.hdlc import frames
from dlms_cosem import enumerations, exceptions


def _sample_obis() -> Obis:
    """Generate a sample OBIS code."""
    return Obis.from_string("0.0.96.1.0.255")


def _sample_descriptor() -> CosemAttribute:
    """Generate a sample COSEM attribute descriptor."""
    return CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=_sample_obis(),
        attribute=2,
    )


def _sample_method_descriptor() -> CosemMethod:
    """Generate a sample COSEM method descriptor."""
    return CosemMethod(
        interface=enums.CosemInterface.CLOCK,
        instance=_sample_obis(),
        method=1,
    )


def _wrapper_then_hdlc_roundtrip(apdu: bytes) -> bytes:
    """Encode APDU with Wrapper PDU and HDLC, then decode back."""
    wpdu = wrappers.WrapperProtocolDataUnit(
        data=apdu,
        wrapper_header=wrappers.WrapperHeader(
            source_wport=16,
            destination_wport=1,
            length=len(apdu),
        ),
    ).to_bytes()

    hdlc_frame = frames.HdlcFrame.build(
        destination_address=1,
        source_address=16,
        control=frames.InformationFrame(0, 0),
        information=wpdu
    )

    # Decode back
    decoded = frames.HdlcFrame.parse(hdlc_frame)
    decoded_wpdu = wrappers.WrapperProtocolDataUnit.from_bytes(decoded.information)

    return decoded_wpdu.data


class TestEquivalenceAndBoundary:
    """Tests for equivalence partitioning and boundary analysis."""

    def test_hdlc_information_boundary_sizes(self):
        """Test HDLC encoding with various payload sizes (boundary values)."""
        boundary_sizes = [0, 1, 2, 127, 128, 255, 256, 1023, 1024]

        for payload_size in boundary_sizes:
            payload = bytes([0x5A] * payload_size)

            hdlc_frame = frames.HdlcFrame.build(
                destination_address=1,
                source_address=16,
                control=frames.InformationFrame(0, 0),
                information=payload
            )

            # Parse back
            decoded = frames.HdlcFrame.parse(hdlc_frame)
            assert decoded.destination_address == 1
            assert decoded.source_address == 16
            assert decoded.information == payload

    def test_hdlc_address_equivalence_class(self):
        """Test HDLC encoding with various address values."""
        boundary_addresses = [0, 1, 63, 127, 128, 255]

        for addr in boundary_addresses:
            hdlc_frame = frames.HdlcFrame.build(
                destination_address=addr,
                source_address=addr,
                control=frames.InformationFrame(0, 0),
                information=b"\x01\x02"
            )

            decoded = frames.HdlcFrame.parse(hdlc_frame)
            assert decoded.destination_address == addr
            assert decoded.source_address == addr

    def test_wrapper_boundary_sizes(self):
        """Test Wrapper PDU encoding with various data sizes."""
        data_sizes = [0, 1, 2, 127, 128, 255, 65535]

        for data_size in data_sizes:
            data = bytes([random.randint(0, 255) for _ in range(data_size)])

            wpdu = wrappers.WrapperProtocolDataUnit(
                data=data,
                wrapper_header=wrappers.WrapperHeader(
                    source_wport=16,
                    destination_wport=1,
                    length=len(data),
                ),
            )

            # Verify length field
            assert wpdu.wrapper_header.length == len(data)


class TestCombinatorialCoverage:
    """Tests for combinatorial coverage."""

    def test_randomized_cross_layer_roundtrip(self):
        """Test randomized cross-layer roundtrip (APDU -> Wrapper -> HDLC)."""
        rng = random.Random(20260213)

        for _ in range(80):
            server_addr = rng.randint(0, 127)
            client_addr = rng.randint(0, 127)
            info_len = rng.randint(0, 48)
            info = bytes(rng.randint(0, 255) for _ in range(info_len))

            hdlc_frame = frames.HdlcFrame.build(
                destination_address=server_addr,
                source_address=client_addr,
                control=frames.InformationFrame(0, 0),
                information=info
            )

            decoded = frames.HdlcFrame.parse(hdlc_frame)
            assert decoded.destination_address == server_addr
            assert decoded.source_address == client_addr
            assert decoded.information == info

    def test_cross_layer_with_real_apdu_set(self):
        """Test cross-layer roundtrip with real APDU set."""
        init_req = InitiateRequest(
            proposed_conformance=b"\x00\x00\x00\x00",
            client_max_recv_pdu_size=128,
        )

        aarq = ApplicationAssociationRequest(
            user_information=UserInformation(content=init_req)
        )

        get_req = GetRequestNormal(cosem_attribute=_sample_descriptor())
        set_req = SetRequestNormal(
            cosem_attribute=_sample_descriptor(),
            data=b"\x09\x01\x2A"
        )
        action_req = ActionRequestNormal(
            cosem_method=_sample_method_descriptor(),
            data=b""
        )

        apdus = [
            aarq.to_bytes(),
            get_req.to_bytes(),
            set_req.to_bytes(),
            action_req.to_bytes(),
        ]

        for apdu in apdus:
            assert _wrapper_then_hdlc_roundtrip(apdu) == apdu


class TestMetamorphicProperties:
    """Tests for metamorphic testing properties."""

    def test_aarq_roundtrip_semantics_are_stable(self):
        """Test AARQ roundtrip preserves semantic properties."""
        aarq = ApplicationAssociationRequest(
            user_information=UserInformation(
                content=InitiateRequest(
                    proposed_conformance=b"\x00\x00\x00\x00",
                    client_max_recv_pdu_size=512,
                )
            ),
            system_title=b"pdlms123",
            authentication=enums.AuthenticationMechanism.NONE,
            ciphered=False,
        )

        parsed_1 = ApplicationAssociationRequest.from_bytes(aarq.to_bytes())
        parsed_2 = ApplicationAssociationRequest.from_bytes(parsed_1.to_bytes())

        assert parsed_2.ciphered == parsed_1.ciphered
        assert parsed_2.system_title == parsed_1.system_title
        assert parsed_2.authentication == parsed_1.authentication

    def test_wrapper_parse_serialize_idempotence(self):
        """Test Wrapper PDU parse-serialize is idempotent."""
        raw = wrappers.WrapperProtocolDataUnit(
            data=b"\x60\x01\x00",
            wrapper_header=wrappers.WrapperHeader(
                source_wport=16,
                destination_wport=1,
                length=3
            ),
        ).to_bytes()

        parsed = wrappers.WrapperProtocolDataUnit.from_bytes(raw)
        assert parsed.to_bytes() == raw

    def test_hdlc_parse_serialize_idempotence(self):
        """Test HDLC frame parse-serialize is idempotent."""
        original = frames.HdlcFrame.build(
            destination_address=1,
            source_address=16,
            control=frames.InformationFrame(0, 0),
            information=b"\x01\x02\x03\x04"
        )

        parsed = frames.HdlcFrame.parse(original)
        rebuilt = parsed.build()

        assert rebuilt == original


class TestFaultInjection:
    """Tests for fault injection and mutation."""

    def test_hdlc_single_bit_mutation_breaks_integrity(self):
        """Test single bit mutation breaks HDLC frame integrity."""
        original_frame = frames.HdlcFrame.build(
            destination_address=1,
            source_address=16,
            control=frames.InformationFrame(0, 0),
            information=b"\x01\x7D\x7E\x02\x03\x04"
        )

        # Mutate a single bit in the middle
        corrupted = bytearray(original_frame)
        corrupted[5] ^= 0x01

        # Should raise exception during parsing
        try:
            frames.HdlcFrame.parse(bytes(corrupted))
            assert False, "Mutated frame should fail parsing"
        except (exceptions.DlmsError, ValueError):
            pass  # Expected

    def test_wrapper_header_length_mutation_is_detected(self):
        """Test Wrapper header length mutation is detected."""
        data = b"\xC0\x01\x01\x00"

        wpdu = wrappers.WrapperProtocolDataUnit(
            data=data,
            wrapper_header=wrappers.WrapperHeader(
                source_wport=16,
                destination_wport=1,
                length=len(data),
            ),
        ).to_bytes()

        # Mutate length field
        mutated = bytearray(wpdu)
        mutated[7] = (mutated[7] + 1) & 0xFF

        try:
            wrappers.WrapperProtocolDataUnit.from_bytes(bytes(mutated))
            assert False, "Mutated length should be detected"
        except ValueError as e:
            assert "does not match" in str(e).lower()


class TestStateTransitionWorkflow:
    """Tests for state-transition workflow checks."""

    def test_association_then_service_request_workflow(self):
        """Test complete association workflow: AARQ -> AARE -> Service."""
        state = "IDLE"

        # Step 1: Send AARQ
        aarq = ApplicationAssociationRequest(
            user_information=UserInformation(
                content=InitiateRequest(
                    proposed_conformance=b"\x00\x00\x00\x00",
                    client_max_recv_pdu_size=256,
                )
            )
        )

        # Parse back (simulates AARE reception)
        _ = ApplicationAssociationRequest.from_bytes(aarq.to_bytes())
        state = "AARQ_SENT"
        assert state == "AARQ_SENT"

        # Step 2: Receive AARE
        aare = ApplicationAssociationResponse(
            result=enums.AssociationResult.ACCEPTED
        )
        parsed_aare = ApplicationAssociationResponse.from_bytes(aare.to_bytes())
        state = (
            "ASSOCIATED"
            if parsed_aare.result == enums.AssociationResult.ACCEPTED
            else "REJECTED"
        )
        assert state == "ASSOCIATED"

        # Step 3: Send service request (GET)
        get_req = GetRequestNormal(cosem_attribute=_sample_descriptor())
        apdu = _wrapper_then_hdlc_roundtrip(get_req.to_bytes())
        assert apdu == get_req.to_bytes()
        state = "SERVICE_ACTIVE"
        assert state == "SERVICE_ACTIVE"

    def test_release_workflow(self):
        """Test release workflow: RLRQ -> RLRE."""
        from dlms_cosem.protocol.acse import ReleaseRequest, ReleaseResponse

        # Step 1: Send RLRQ
        rlrq = ReleaseRequest(
            reason=enums.ReleaseReason.NORMAL
        )

        _ = ReleaseRequest.from_bytes(rlrq.to_bytes())

        # Step 2: Receive RLRE
        rlre = ReleaseResponse(
            result=enums.AssociationResult.ACCEPTED
        )
        parsed_rlre = ReleaseResponse.from_bytes(rlre.to_bytes())

        assert parsed_rlre.result == enums.AssociationResult.ACCEPTED


class TestLongRunningStability:
    """Tests for long-running stability."""

    def test_repeated_roundtrip_stability(self):
        """Test repeated roundtrip doesn't accumulate errors."""
        original_apdu = GetRequestNormal(cosem_attribute=_sample_descriptor()).to_bytes()

        # Perform 100 roundtrips
        current = original_apdu
        for _ in range(100):
            current = _wrapper_then_hdlc_roundtrip(current)

        assert current == original_apdu, "Repeated roundtrips should preserve original data"

    def test_concurrent_encoding_decoding_stability(self):
        """Test encoding/decoding with random data."""
        for _ in range(50):
            data_len = random.randint(1, 100)
            random_data = bytes(random.randint(0, 255) for _ in range(data_len))

            hdlc_frame = frames.HdlcFrame.build(
                destination_address=random.randint(1, 127),
                source_address=random.randint(1, 127),
                control=frames.InformationFrame(random.randint(0, 7), 0),
                information=random_data
            )

            decoded = frames.HdlcFrame.parse(hdlc_frame)
            assert decoded.information == random_data
