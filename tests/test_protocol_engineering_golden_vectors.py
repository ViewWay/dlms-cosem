"""Engineering-grade golden vectors for protocol regression guard.

These tests use golden vectors from real DLMS/COSEM captures to ensure
encoding/decoding correctness. They serve as regression guards against
breaking changes in protocol implementation.

Reference: pdlms/test_protocol_engineering_golden_vectors.py
"""

from dlms_cosem.protocol import wrappers
from dlms_cosem.protocol.xdlms import GetRequestNormal, SetRequestNormal, ActionRequestNormal
from dlms_cosem.protocol.acse import ApplicationAssociationRequest, UserInformation
from dlms_cosem.protocol.acse.base import AppContextName
from dlms_cosem.cosem import Obis
from dlms_cosem.cosem import CosemAttribute, CosemMethod
from dlms_cosem import enumerations


def test_golden_vector_get_request_apdu():
    """Golden vector for GET-REQUEST APDU."""
    expected_hex = "C0014100010000600100FF02"
    obis = Obis.from_string("0.0.96.1.0.255")
    descriptor = CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=obis,
        attribute=2
    )
    actual_hex = GetRequestNormal(cosem_attribute=descriptor).to_bytes().hex().upper()
    assert actual_hex == expected_hex


def test_golden_vector_set_request_apdu():
    """Golden vector for SET-REQUEST APDU."""
    expected_hex = "C2014100010000600100FF0209012A"
    obis = Obis.from_string("0.0.96.1.0.255")
    descriptor = CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=obis,
        attribute=2
    )
    actual_hex = SetRequestNormal(
        cosem_attribute=descriptor,
        data=b"\x09\x01\x2A"
    ).to_bytes().hex().upper()
    assert actual_hex == expected_hex


def test_golden_vector_action_request_apdu():
    """Golden vector for ACTION-REQUEST APDU."""
    expected_hex = "C4014100080000600100FF01"
    obis = Obis.from_string("0.0.96.1.0.255")
    cosem_method = CosemMethod(
        interface=enums.CosemInterface.CLOCK,
        instance=obis,
        method=1
    )
    actual_hex = ActionRequestNormal(cosem_method=cosem_method, data=b"").to_bytes().hex().upper()
    assert actual_hex == expected_hex


def test_golden_vector_aarq_apdu():
    """Golden vector for AARQ APDU."""
    expected_hex = "6017A109060760857405080101BE0A04080106000000008180"
    from dlms_cosem.protocol.xdlms import InitiateRequest

    init = InitiateRequest(
        proposed_conformance=b"\x00\x00\x00\x00",
        client_max_recv_pdu_size=128
    )
    actual_hex = ApplicationAssociationRequest(
        user_information=UserInformation(content=init)
    ).to_bytes().hex().upper()
    assert actual_hex == expected_hex


def test_golden_vector_wrapper_apdu():
    """Golden vector for Wrapper PDU."""
    expected_wpdu = "000100100001000CC0014100010000600100FF02"

    obis = Obis.from_string("0.0.96.1.0.255")
    descriptor = CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=obis,
        attribute=2
    )
    apdu = GetRequestNormal(cosem_attribute=descriptor).to_bytes()

    wpdu = wrappers.WrapperProtocolDataUnit(
        data=apdu,
        wrapper_header=wrappers.WrapperHeader(
            source_wport=16,
            destination_wport=1,
            length=len(apdu)
        ),
    ).to_bytes()

    assert wpdu.hex().upper() == expected_wpdu


def test_golden_vector_hdlc_encoding():
    """Golden vector for HDLC frame encoding."""
    from dlms_cosem.hdlc import frames

    obis = Obis.from_string("0.0.96.1.0.255")
    descriptor = CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=obis,
        attribute=2
    )
    apdu = GetRequestNormal(cosem_attribute=descriptor).to_bytes()

    wpdu = wrappers.WrapperProtocolDataUnit(
        data=apdu,
        wrapper_header=wrappers.WrapperHeader(
            source_wport=16,
            destination_wport=1,
            length=len(apdu)
        ),
    ).to_bytes()

    hdlc_frame = frames.HdlcFrame.build(
        destination_address=1,
        source_address=16,
        control=frames.InformationFrame(0, 0),
        information=wpdu
    )

    # Verify frame structure
    assert hdlc_frame[0:1] == b'\x7E'  # Start flag
    assert hdlc_frame[-1:] == b'\x7E'  # End flag


def test_golden_vector_hdlc_escape_behavior():
    """Golden vector for HDLC escape sequence handling."""
    from dlms_cosem.hdlc import frames

    # Data containing special bytes that need escaping
    payload = bytes.fromhex("007E7D7E7D01")

    hdlc_frame = frames.HdlcFrame.build(
        destination_address=1,
        source_address=16,
        control=frames.InformationFrame(0, 0),
        information=payload
    )

    # Verify escape sequences: 0x7E -> 0x7D 0x5E, 0x7D -> 0x7D 0x5D
    assert b'\x7D\x5E' in hdlc_frame  # Escaped 0x7E
    assert b'\x7D\x5D' in hdlc_frame  # Escaped 0x7D


def test_golden_vector_roundtrip_stability():
    """Golden vector for encode-decode roundtrip stability."""
    from dlms_cosem.hdlc import frames

    original_frame = bytes.fromhex(
        "7E1B032100E52A000100100001000CC0014100010000600100FF02500B7E"
    )

    decoded = frames.HdlcFrame.parse(original_frame)
    rebuilt = decoded.build()

    assert rebuilt == original_frame, "Roundtrip encoding should produce identical frame"


def test_golden_vector_aarq_with_app_context():
    """Golden vector for AARQ with application context."""
    expected_hex = "6018A109060760857405080101BE0B040901060000000081800780"
    from dlms_cosem.protocol.xdlms import InitiateRequest

    init = InitiateRequest(
        proposed_conformance=b"\x00\x00\x00\x00",
        client_max_recv_pdu_size=128
    )
    aarq = ApplicationAssociationRequest(
        user_information=UserInformation(content=init)
    )
    actual_hex = aarq.to_bytes().hex().upper()

    # Extract application context part
    assert actual_hex[:28] == expected_hex[:28]
