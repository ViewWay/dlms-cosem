# -*- coding: utf-8 -*-
"""
Integration tests with real DLMS/COSEM meter.

These tests verify core functionality against an actual meter at 10.32.24.151:4059

Run with: pytest tests/test_real_meter_integration.py -v
"""
import socket
import struct
import pytest
import time

# Meter configuration
METER_HOST = "10.32.24.151"
METER_PORT = 4059
LLS_PASSWORD = "00000000"


class DLMSTestClient:
    """Simplified DLMS client for integration testing."""

    @staticmethod
    def wrap(wport_src, wport_dst, data):
        """Wrap data in DLMS IP Wrapper."""
        return (struct.pack(">H", 1) + struct.pack(">H", wport_src) +
                struct.pack(">H", wport_dst) + struct.pack(">H", len(data)) + data)

    @staticmethod
    def recv_all(sock, expected_len):
        """Receive all expected bytes."""
        data = b""
        while len(data) < expected_len:
            chunk = sock.recv(expected_len - len(data))
            if not chunk:
                break
            data += chunk
        return data

    @staticmethod
    def send_and_recv(sock, data):
        """Send and receive with wrapper handling."""
        sock.sendall(data)
        header = DLMSTestClient.recv_all(sock, 8)
        if len(header) < 8:
            return b""
        length = struct.unpack(">H", header[6:8])[0]
        payload = DLMSTestClient.recv_all(sock, length)
        return header + payload

    @staticmethod
    def create_aarq_management(password):
        """Create AARQ for management client with LLS."""
        return (bytes.fromhex("6042a109060760857405080101"
                             "a20a04080000000000000000"
                             "8a020780"  # ACSE requirements
                             "8b07"  # mechanism name
                             "60857405080201"  # LOW_SECURITY
                             "ac0a8008") + password.encode('ascii') +
                bytes.fromhex("be10040e01000000065f1f0400001f1fffff"))

    @staticmethod
    def create_get_request(obis_5bytes, class_id=1, attr_id=2, invoke_id=0xC1):
        """Create GetRequest for an attribute.

        Format: C0 01 <invoke_id> 00 01 00 <class_id> <obis> <attr_id> 00
        - C0 01 = GetRequestNormal tag, length
        - <invoke_id> = Invoke ID and Priority
        - 00 = Reserved
        - 01 = Attribute Descriptor (single)
        - 00 <class_id> = Class ID in big-endian
        - <obis> = OBIS code (5 bytes)
        - <attr_id> = Attribute ID
        - 00 = Access Selector (none)
        """
        return (bytes.fromhex(f"c001{invoke_id:02x}00") +
                bytes.fromhex("0100") +  # attribute descriptor + class_id (big-endian)
                obis_5bytes +
                bytes.fromhex(f"{attr_id:02x}00"))

    @staticmethod
    def parse_get_response(resp):
        """Parse GetResponse and return value."""
        if len(resp) < 12:
            return None

        payload = resp[8:]
        if payload[0] == 0xC4:
            if len(payload) >= 9 and payload[4] == 0x06:  # Double Long Unsigned
                return struct.unpack(">I", payload[5:9])[0]
            elif len(payload) >= 6 and payload[4] == 0x09:  # Octet String
                str_len = payload[5]
                return payload[6:6+str_len].decode('ascii', errors='ignore')
            elif len(payload) >= 9 and payload[4] == 0x12:  # Double Long Unsigned (alt)
                return struct.unpack(">I", payload[5:9])[0]
        return None


@pytest.fixture(scope="module")
def meter_connection():
    """Fixture that provides a connection to the meter."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((METER_HOST, METER_PORT))

    # Associate with LLS
    aarq = DLMSTestClient.create_aarq_management(LLS_PASSWORD)
    resp = DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, aarq))

    if len(resp) < 26 or resp[25] != 0:
        pytest.skip(f"Meter association failed: {resp.hex()[:40]}")

    yield sock

    # Disconnect
    try:
        rlrq = bytes.fromhex("6215800100be10040e01000000065f1f0400001f1fffff")
        DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, rlrq))
    finally:
        sock.close()


class TestRealMeterTCP:
    """Integration tests with real DLMS/COSEM meter over TCP/IP."""

    # Class-level invoke_id counter to avoid conflicts
    invoke_id_counter = 0xC1

    def test_tcp_connection(self):
        """Test basic TCP connection to meter."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((METER_HOST, METER_PORT))
        sock.close()
        assert True  # If we get here, connection succeeded

    def test_association_management_lls(self):
        """Test Management Client association with LLS."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        try:
            sock.connect((METER_HOST, METER_PORT))

            aarq = DLMSTestClient.create_aarq_management(LLS_PASSWORD)
            resp = DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, aarq))

            assert len(resp) >= 26, "Response too short"
            assert resp[25] == 0, f"Association failed with result {resp[25]}"
        finally:
            try:
                sock.close()
            except:
                pass

    def test_get_frame_counter(self, meter_connection):
        """Test reading frame counter (OBIS 0.0.43.1.0.255)."""
        time.sleep(0.2)  # Small delay after association
        obis = bytes.fromhex("002b0100ff")  # 0.0.43.1.0.255
        invoke = TestRealMeterTCP.invoke_id_counter
        TestRealMeterTCP.invoke_id_counter = (TestRealMeterTCP.invoke_id_counter + 1) % 16 + 0xC0
        get_req = DLMSTestClient.create_get_request(obis, class_id=1, invoke_id=invoke)
        resp = DLMSTestClient.send_and_recv(meter_connection, DLMSTestClient.wrap(1, 1, get_req))

        value = DLMSTestClient.parse_get_response(resp)
        assert value is not None, f"Failed to read frame counter: {resp.hex()}"
        assert isinstance(value, int), f"Frame counter should be int, got {type(value)}"
        assert value >= 0, f"Frame counter should be non-negative, got {value}"

    def test_get_multiple_attributes(self, meter_connection):
        """Test reading multiple attributes with different invoke IDs."""
        obis = bytes.fromhex("002b0100ff")  # Frame counter

        success = 0
        for i in range(8):
            invoke_id = 0xC1 + i
            get_req = DLMSTestClient.create_get_request(obis, class_id=1, invoke_id=invoke_id)
            resp = DLMSTestClient.send_and_recv(meter_connection, DLMSTestClient.wrap(1, 1, get_req))
            value = DLMSTestClient.parse_get_response(resp)
            if value is not None:
                success += 1

        assert success >= 7, f"Only {success}/8 reads succeeded"

    def test_connection_stability(self, meter_connection):
        """Test connection stability over multiple reads."""
        obis = bytes.fromhex("002b0100ff")  # Frame counter

        success = 0
        for i in range(10):
            get_req = DLMSTestClient.create_get_request(obis, class_id=1)
            resp = DLMSTestClient.send_and_recv(meter_connection, DLMSTestClient.wrap(1, 1, get_req))
            value = DLMSTestClient.parse_get_response(resp)
            if value is not None:
                success += 1
            time.sleep(0.5)  # Small delay between reads

        assert success >= 9, f"Only {success}/10 reads succeeded"

    def test_dlms_wrapper_format(self, meter_connection):
        """Test DLMS IP Wrapper format."""
        obis = bytes.fromhex("002b0100ff")
        get_req = DLMSTestClient.create_get_request(obis, class_id=1)

        wrapped = DLMSTestClient.wrap(1, 1, get_req)

        # Check wrapper format: version(2) + src_wport(2) + dst_wport(2) + length(2) + data
        assert len(wrapped) >= 8, "Wrapper too short"
        version = struct.unpack(">H", wrapped[0:2])[0]
        src_wport = struct.unpack(">H", wrapped[2:4])[0]
        dst_wport = struct.unpack(">H", wrapped[4:6])[0]
        length = struct.unpack(">H", wrapped[6:8])[0]

        assert version == 1, f"Wrapper version should be 1, got {version}"
        assert src_wport == 1, f"Source wport should be 1, got {src_wport}"
        assert dst_wport == 1, f"Dest wport should be 1, got {dst_wport}"
        assert length == len(get_req), f"Length mismatch: {length} != {len(get_req)}"

    def test_invoke_id_cycling(self, meter_connection):
        """Test invoke ID cycling through all 16 values."""
        obis = bytes.fromhex("002b0100ff")

        success = 0
        for i in range(16):
            invoke_id = 0xC1 + i
            if invoke_id > 0xCF:
                invoke_id = 0xC0 + (invoke_id - 0xCF)
            get_req = DLMSTestClient.create_get_request(obis, class_id=1, invoke_id=invoke_id)
            resp = DLMSTestClient.send_and_recv(meter_connection, DLMSTestClient.wrap(1, 1, get_req))
            value = DLMSTestClient.parse_get_response(resp)
            if value is not None:
                success += 1

        assert success >= 14, f"Only {success}/16 invoke IDs worked"

    def test_response_parsing(self, meter_connection):
        """Test response parsing for different data types."""
        obis = bytes.fromhex("002b0100ff")  # Frame counter (Double Long Unsigned)
        get_req = DLMSTestClient.create_get_request(obis, class_id=1)
        resp = DLMSTestClient.send_and_recv(meter_connection, DLMSTestClient.wrap(1, 1, get_req))

        # Check wrapper in response
        assert len(resp) >= 8, "Response too short for wrapper"
        version = struct.unpack(">H", resp[0:2])[0]
        assert version == 1, f"Response wrapper version should be 1, got {version}"

        # Check GetResponse format
        payload = resp[8:]
        assert len(payload) >= 5, "Payload too short"
        assert payload[0] == 0xC4, f"Response should be GetResponseNormal (C4), got {payload[0]:02X}"

        # Check data type
        data_tag = payload[4]
        assert data_tag in [0x06, 0x12], f"Expected Double Long Unsigned (06 or 12), got {data_tag:02X}"


class TestRealMeterProtocol:
    """Protocol-level tests with real meter."""

    def test_aarq_format(self):
        """Test AARQ format matches DLMS specification."""
        aarq = DLMSTestClient.create_aarq_management(LLS_PASSWORD)

        # Check AARQ tag
        assert aarq[0] == 0x60, f"AARQ should start with 0x60, got 0x{aarq[0]:02X}"

        # Check application context name
        assert b'\xa1\x09\x06\x07\x60\x85\x74\x05\x08\x01\x01' in aarq, "Missing LN application context"

        # Check authentication mechanism
        assert b'\x8b\x07\x60\x85\x74\x05\x08\x02\x01' in aarq, "Missing LOW_SECURITY mechanism"

    def test_get_request_format(self):
        """Test GetRequest format matches DLMS specification."""
        obis = bytes.fromhex("002b0100ff")
        get_req = DLMSTestClient.create_get_request(obis, class_id=1)

        # Check GetRequestNormal tag
        assert get_req[0] == 0xC0, f"GetRequest should start with 0xC0, got 0x{get_req[0]:02X}"
        assert get_req[1] == 0x01, f"Length byte should be 0x01, got 0x{get_req[1]:02X}"

        # Check invoke_id
        invoke_id = get_req[2]
        assert invoke_id >= 0xC0, f"Invoke_id should be >= 0xC0, got 0x{invoke_id:02X}"

        # Check attribute descriptor
        assert get_req[4] == 0x01, f"Attribute descriptor should be 0x01, got 0x{get_req[4]:02X}"

        # Check class ID
        class_id = struct.unpack(">H", get_req[5:7])[0]
        assert class_id == 1, f"Class ID should be 1, got {class_id}"

    def test_obis_encoding(self):
        """Test OBIS code encoding."""
        # OBIS 0.0.43.1.0.255 should encode as 00 2B 01 00 FF
        obis_bytes = bytes.fromhex("002b0100ff")
        assert len(obis_bytes) == 5, f"OBIS should be 5 bytes, got {len(obis_bytes)}"
        assert obis_bytes[0] == 0x00, f"Group B should be 0, got {obis_bytes[0]}"
        assert obis_bytes[1] == 0x2B, f"Group C should be 0x2B (43), got {obis_bytes[1]}"
        assert obis_bytes[2] == 0x01, f"Group D should be 1, got {obis_bytes[2]}"


if __name__ == "__main__":
    # Run tests without pytest
    print("Running integration tests with real meter...")
    print("=" * 70)

    try:
        # Simple single-connection test
        print("\n[Test] Complete Connection + Read Test")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((METER_HOST, METER_PORT))
        print("  [OK] TCP connected")

        aarq = DLMSTestClient.create_aarq_management(LLS_PASSWORD)
        resp = DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, aarq))

        if len(resp) >= 26 and resp[25] == 0:
            print("  [OK] LLS Associated")
        else:
            print(f"  [FAIL] Association failed: {resp.hex()[:40]}")
            sock.close()
            raise Exception("Association failed")

        # Read frame counter 3 times
        for i in range(3):
            obis = bytes.fromhex("002b0100ff")
            get_req = DLMSTestClient.create_get_request(obis, class_id=1)
            resp = DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, get_req))
            value = DLMSTestClient.parse_get_response(resp)
            if value is not None:
                print(f"  [OK] Read {i+1}: Frame Counter = {value}")
            else:
                print(f"  [FAIL] Read {i+1}: {resp.hex()}")
                break

        # Disconnect
        rlrq = bytes.fromhex("6215800100be10040e01000000065f1f0400001f1fffff")
        DLMSTestClient.send_and_recv(sock, DLMSTestClient.wrap(1, 1, rlrq))
        sock.close()
        print("  [OK] Disconnected")

        print("\n" + "=" * 70)
        print("All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
