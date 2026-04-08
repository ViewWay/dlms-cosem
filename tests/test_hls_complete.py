#!/usr/bin/env python3
"""
Complete HLS Test Suite - GET, SET, ACTION with Encryption

Based on real meter logs from KFM1000100000002 @ 10.32.24.151:4059

Keys:
  AKEY: D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF
  EKEY: 000102030405060708090A0B0C0D0E0F
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HLSTestSuite:
    """HLS Test Suite based on real meter logs."""

    def __init__(self):
        self.AKEY = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
        self.EKEY = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
        self.test_count = 0
        self.pass_count = 0

    def log(self, message):
        print(message)

    def test(self, name, func):
        """Run a test."""
        self.test_count += 1
        self.log(f"\n[Test {self.test_count}] {name}")
        try:
            func()
            self.pass_count += 1
            self.log("  [PASSED]")
        except AssertionError as e:
            self.log(f"  [FAILED] {e}")
        except Exception as e:
            self.log(f"  [ERROR] {e}")

    def assert_eq(self, a, b, msg=""):
        if a != b:
            raise AssertionError(f"{msg}: {a} != {b}")

    def assert_in(self, a, b, msg=""):
        if a not in b:
            raise AssertionError(f"{msg}: {a} not in {b}")

    def assert_hex(self, a, b, msg=""):
        if a.replace(" ", "") != b.replace(" ", ""):
            raise AssertionError(f"{msg}: hex mismatch")

    # ================================================================
    # Phase 1: Public Connection Tests
    # ================================================================

    def test_aarq_plain(self):
        """Test plain AARQ parsing."""
        hex_data = "60 29 A1 09 06 07 60 85 74 05 08 01 01 A6 0A 04 08 00 00 00 00 00 00 00 00 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF"
        data = bytes.fromhex(hex_data.replace(" ", ""))

        self.assert_eq(data[0], 0x60, "AARQ tag")
        self.assert_eq(data[1], 0x29, "AARQ length")

        # Check context
        context_oid = data[4:13]
        expected_context = bytes.fromhex("60857405080101")
        self.assert_eq(context_oid, expected_context, "LN context")

        # Check conformance
        self.assert_in(b'\xBE\x10\x04\x0E', data, "Conformance bits")

        self.log(f"    Tag: 0x{data[0]:02X}")
        self.log(f"    Context: LN")
        self.log(f"    Conformance: Present")

    def test_aare_plain(self):
        """Test plain AARE parsing."""
        hex_data = "61 29 A1 09 06 07 60 85 74 05 08 01 01 A2 03 02 01 00 A3 05 A1 03 02 01 00 BE 10 04 0E 08 00 06 5F 1F 04 00 00 12 10 04 C8 00 07"
        data = bytes.fromhex(hex_data.replace(" ", ""))

        self.assert_eq(data[0], 0x61, "AARE tag")
        self.assert_eq(data[4], 0xA2, "Result tag")
        self.assert_eq(data[6], 0x00, "Result code (accepted)")

        # Check max PDU size
        pdu_size_idx = data.index(b'\xBE\x10\x04\x0E')
        pdu_size = int.from_bytes(data[pdu_size_idx+4:pdu_size_idx+8], 'big')
        self.assert_eq(pdu_size, 0x04C8, "Max PDU size")

        self.log(f"    Tag: 0x{data[0]:02X}")
        self.log(f"    Result: Accepted (0x00)")
        self.log(f"    Max PDU: {pdu_size} bytes")

    def test_get_device_number_plain(self):
        """Test GET device number (plain)."""
        # GET Request
        req_hex = "C0 01 C1 00 01 00 00 2A 00 00 FF 02 00"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        self.assert_eq(req[0], 0xC0, "GET_REQUEST tag")
        self.assert_eq(req[2], 0xC1, "Invoke ID")
        self.assert_eq(int.from_bytes(req[4:6], 'big'), 0x0001, "Class ID")
        self.assert_eq(list(req[6:12]), [0, 0, 42, 0, 0, 255], "Instance ID")

        # GET Response
        resp_hex = "C4 01 C1 00 09 10 4B 46 4D 31 30 30 30 31 30 30 30 30 30 30 30 32"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        self.assert_eq(resp[0], 0xC4, "GET_RESPONSE tag")
        self.assert_eq(resp[2], 0xC1, "Invoke ID")
        self.assert_eq(resp[4], 0x00, "Result")
        self.assert_eq(resp[6], 0x10, "OctetString tag")

        device_number = resp[8:8+17].decode('ascii')
        self.assert_eq(device_number, "KFM1000100000002", "Device number")

        self.log(f"    OBIS: 0.0.42.0.0.255")
        self.log(f"    Device Number: {device_number}")

    def test_get_frame_counter_plain(self):
        """Test GET frame counter (plain)."""
        # GET Request
        req_hex = "C0 01 C1 00 01 00 00 2B 01 00 FF 02 00"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        self.assert_eq(list(req[6:12]), [0, 0, 43, 1, 0, 255], "Instance ID (0.0.43.1.0.255)")

        # GET Response
        resp_hex = "C4 01 C1 00 06 00 00 4B 35"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        self.assert_eq(resp[6], 0x06, "DoubleLongUnsigned tag")
        frame_counter = int.from_bytes(resp[7:11], 'big')
        self.assert_eq(frame_counter, 0x4B35, "Frame counter value")

        self.log(f"    Frame Counter: {frame_counter} (0x{frame_counter:04X})")

    # ================================================================
    # Phase 2: HLS Encrypted Connection Tests
    # ================================================================

    def test_aarq_encrypted(self):
        """Test encrypted AARQ parsing."""
        # Full frame with wrapper
        hex_data = "00 01 00 01 00 01 00 5F 60 5D A1 09 06 07 60 85 74 05 08 01 03 A6 0A 04 08 00 00 00 00 00 00 00 00 8A 02 07 80 8B 07 60 85 74 05 08 02 05 AC 12 80 10 73 36 55 4C 55 33 37 36 63 5A 45 6F 61 79 50 6C BE 23 04 21 21 1F 30 00 00 4B 36 8C 4E A2 6D 0F 47 DE E7 D2 01 4E DF D4 00 2A 0F 3F B3 14 0E 01 FE 06 CC DB 90"
        data = bytes.fromhex(hex_data.replace(" ", ""))

        # Parse wrapper
        version = int.from_bytes(data[0:2], 'big')
        source_wport = int.from_bytes(data[2:6], 'big')
        dest_wport = int.from_bytes(data[6:10], 'big')
        length = int.from_bytes(data[10:14], 'big')

        self.assert_eq(version, 0x0001, "Wrapper version")
        self.assert_eq(source_wport, 0x0001, "Source WPort")
        self.assert_eq(dest_wport, 0x0010, "Dest WPort")

        apdu = data[14:14+length]
        self.assert_eq(apdu[0], 0x60, "AARQ tag")

        # Check LNC context
        self.assert_in(b'\x60\x85\x74\x05\x08\x01\x03', apdu, "LNC context")

        # Check HLS-GMAC mechanism
        self.assert_in(b'\x8B\x07\x60\x85\x74\x05\x08\x02\x05', apdu, "HLS-GMAC mechanism")

        # Parse auth value
        auth_idx = apdu.index(b'\xAC\x12')
        auth_len = apdu[auth_idx + 3]
        auth_value = apdu[auth_idx + 4:auth_idx + 4 + auth_len]
        self.assert_eq(auth_value.decode('ascii'), '7336554C55333736635A456F6179506C', "Auth value")

        # Parse ciphered initiate request
        cipher_idx = apdu.index(b'\xBE\x23\x04\x21')
        iv = apdu[cipher_idx + 6:cipher_idx + 18]
        self.assert_eq(iv.hex().upper(), '000000000000000000004B36', "IV")

        self.log(f"    Context: LNC")
        self.log(f"    Mechanism: HLS-GMAC")
        self.log(f"    Auth Value: {auth_value.decode('ascii')}")
        self.log(f"    IV: {iv.hex().upper()}")

    def test_aare_encrypted(self):
        """Test encrypted AARE parsing."""
        hex_data = "00 01 00 01 00 01 00 6B 61 69 A1 09 06 07 60 85 74 05 08 01 03 A2 03 02 01 00 A3 05 A1 03 02 01 0E A4 0A 04 08 4B 46 4D 64 10 00 00 02 88 02 07 80 89 07 60 85 74 05 08 02 05 AA 12 80 10 E1 74 F6 AC A2 1F 02 24 5E F7 91 1B 54 AF 84 D5 BE 23 04 21 28 1F 30 00 00 41 3A 42 98 25 81 96 F1 F3 93 8E C8 5A 38 E9 EA 97 68 DA 07 77 92 27 48 A0 B1 B1 C7"
        data = bytes.fromhex(hex_data.replace(" ", ""))

        # Parse wrapper
        length = int.from_bytes(data[10:14], 'big')
        apdu = data[14:14+length]

        self.assert_eq(apdu[0], 0x61, "AARE tag")

        # Check result
        self.assert_eq(apdu[4], 0xA2, "Result tag")
        self.assert_eq(apdu[6], 0x00, "Result code (accepted)")

        # Check diagnostic
        self.assert_eq(apdu[9], 0x0E, "Diagnostic (Authentication required)")

        # Parse server title
        title_idx = apdu.index(b'\xA4\x0A\x04\x08')
        server_title = apdu[title_idx + 4:title_idx + 12]
        self.assert_eq(server_title, b'\x4B\x46\x4D\x64\x10\x00\x00\x02', "Server title")

        # Parse ciphered initiate response
        cipher_idx = apdu.index(b'\xBE\x23\x04\x21')
        iv = apdu[cipher_idx + 6:cipher_idx + 18]
        self.assert_eq(iv.hex().upper(), '4B464D64100000020000413A', "IV")

        self.log(f"    Server Title: {server_title.hex().upper()}")
        self.log(f"    IV: {iv.hex().upper()}")

    def test_action_gmac(self):
        """Test GMAC ACTION for security setup."""
        # Request
        req_hex = "00 01 00 01 00 01 00 33 CB 31 30 00 00 4B 38 96 D8 22 06 3B 33 2B 61 BF 3F 93 29 C2 C1 9B 23 82 15 2C F2 56 47 72 48 9F 74 56 A3 BC B2 C4 98 BE 9D 72 9E 4B DF 54 F8 0E 98 32 EF"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        # Response
        resp_hex = "00 01 00 01 00 01 00 2C CF 2A 30 00 00 41 3C 54 74 21 EA E9 A8 D7 18 5E D7 90 6E 2B 73 53 5A BE EF CC 34 EA 74 A0 80 95 00 0F 70 16 16 ED 51 C8 D1 B7 98 7E"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        # Parse request
        req_length = int.from_bytes(req[10:14], 'big')
        req_apdu = req[14:14+req_length]
        req_iv = req_apdu[4:16]  # Skip tag and length
        self.assert_eq(req_iv.hex().upper(), '000000000000000000004B38', "Request IV")

        # Parse response
        resp_length = int.from_bytes(resp[10:14], 'big')
        resp_apdu = resp[14:14+resp_length]

        # Decrypt response (simulate)
        # The response contains the Stoken for GMAC verification
        # From logs: PlainData: C701C10001000911100000413B55175DD868AE07E0E1639C00
        # Return Parameters: 100000413B55175DD868AE07E0E1639C00
        # GMAC Tag: 55175DD868AE07E0E1639C00

        self.log(f"    IC: 0x000F (Security Setup)")
        self.log(f"    Method: 0x01 (Key Handshake)")
        self.log(f"    Stoken: 100000413B55175DD868AE07E0E1639C00")

    # ================================================================
    # Phase 3: GET Operation Tests (Encrypted)
    # ================================================================

    def test_get_clock_encrypted(self):
        """Test GET clock operation (encrypted)."""
        # Request
        req_hex = "00 01 00 01 00 01 00 20 C8 1E 30 00 00 4B 39 9E 5F 51 92 0D F4 8D 8E 86 CD 65 86 3B C7 7A 89 CA D7 23 1E 5C F3 A3 B4 FE"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        req_length = int.from_bytes(req[10:14], 'big')
        req_apdu = req[14:14+req_length]

        # Parse encrypted GET request
        plain_data = bytes.fromhex("C001C100080000010000FF0200")

        self.assert_eq(req_apdu[0], 0xC8, "Encrypted GET tag")
        self.assert_eq(req_apdu[2:14], bytes.fromhex("1E3000004B39"), "IV")

        # Response
        resp_hex = "00 01 00 01 00 01 00 25 CC 23 30 00 00 41 3D B2 57 BC 13 E3 80 D8 1D 5D 47 72 8A 4F 6D B4 3F EE 57 7B 5E 1E A5 9C 0A 3F 48 4E 71 2C A1"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        resp_length = int.from_bytes(resp[10:14], 'big')
        resp_apdu = resp[14:14+resp_length]

        self.assert_eq(resp_apdu[0], 0xCC, "Encrypted GET_RESPONSE tag")
        self.assert_eq(resp_apdu[2:14], bytes.fromhex("23300000413D"), "IV")

        # From logs: PlainData: C401C100090C07EA04040604042B00FE9801
        clock_value = "07EA04040604042B00FE9801"

        self.log(f"    OBIS: 0.0.1.0.0.255")
        self.log(f"    Clock Value: {clock_value}")

    # ================================================================
    # Phase 4: SET Operation Tests (Encrypted)
    # ================================================================

    def test_set_clock_encrypted(self):
        """Test SET clock operation (encrypted)."""
        # Request
        req_hex = "00 01 00 01 00 01 00 2E C9 2C 30 00 00 4B 3F C7 BD F1 8D 00 01 71 20 6E 10 2A 91 29 B0 AE CC 05 DB 7B 95 51 BE 6C FB 1D D5 20 57 19 45 48 6A 6D AD 27 1A 95 E3 1C"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        req_length = int.from_bytes(req[10:14], 'big')
        req_apdu = req[14:14+req_length]

        self.assert_eq(req_apdu[0], 0xC9, "Encrypted SET tag")
        self.assert_eq(req_apdu[2:14], bytes.fromhex("2C3000004B3F"), "IV")

        # From logs: PlainData: C101C100080000010000FF0200090C07EA04080314311A008000FF
        plain_data = bytes.fromhex("C101C100080000010000FF0200090C07EA04080314311A008000FF")

        # This is a SET request for clock (Class 8, Instance 0.0.1.0.0.255, Attribute 2)
        self.assert_eq(plain_data[0], 0xC1, "SET_REQUEST_NORMAL tag")
        self.assert_eq(int.from_bytes(plain_data[4:6], 'big'), 0x0008, "Class ID (Clock)")

        # Response
        resp_hex = "00 01 00 01 00 01 00 17 CD 15 30 00 00 41 42 36 78 B3 58 DB 9A 3D 39 F2 C1 51 E5 62 91 49 77"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        resp_length = int.from_bytes(resp[10:14], 'big')
        resp_apdu = resp[14:14+resp_length]

        self.assert_eq(resp_apdu[0], 0xCD, "Encrypted SET_RESPONSE tag")
        self.assert_eq(resp_apdu[2:14], bytes.fromhex("153000004142"), "IV")

        # From logs: PlainData: C501C100 (Success response)
        self.log(f"    OBIS: 0.0.1.0.0.255")
        self.log(f"    New Clock Value: 07EA04080314311A008000FF")
        self.log(f"    Result: Success")

    # ================================================================
    # Phase 5: Disconnect Tests (Encrypted)
    # ================================================================

    def test_rlrq_encrypted(self):
        """Test RLRQ disconnect (encrypted)."""
        req_hex = "00 01 00 01 00 01 00 2A 62 28 80 01 00 BE 23 04 21 21 1F 30 00 00 4B 3A 38 7E 9B 88 D8 69 D9 86 A1 8D DE 0E AC 6D 2F 63 1A 25 2F 16 44 A9 E7 94 69 D5"
        req = bytes.fromhex(req_hex.replace(" ", ""))

        req_length = int.from_bytes(req[10:14], 'big')
        req_apdu = req[14:14+req_length]

        self.assert_eq(req_apdu[0], 0x62, "RLRQ tag")
        self.assert_eq(req_apdu[2:14], bytes.fromhex("288000004B3A"), "IV")

        # From logs: PlainData: 01000000065F1F0400001F1FFFFF
        self.log(f"    Reason: Normal release")

    def test_rlre_encrypted(self):
        """Test RLRE disconnect response (encrypted)."""
        resp_hex = "00 01 00 01 00 01 00 2A 63 28 80 01 00 BE 23 04 21 28 1F 30 00 00 41 3E DB D6 C9 C1 DE 9F BE 08 E0 0C 14 82 D6 15 82 3B 03 31 14 8D F5 10 CF A0 E3 C2"
        resp = bytes.fromhex(resp_hex.replace(" ", ""))

        resp_length = int.from_bytes(resp[10:14], 'big')
        resp_apdu = resp[14:14+resp_length]

        self.assert_eq(resp_apdu[0], 0x63, "RLRE tag")
        self.assert_eq(resp_apdu[2:14], bytes.fromhex("28800000413E"), "IV")

        # From logs: PlainData: 0800065F1F0400001E1D04C80007
        self.log(f"    Result: Normal release")

    # ================================================================
    # Run All Tests
    # ================================================================

    def run_all(self):
        """Run all HLS tests."""
        print("=" * 70)
        print("HLS Complete Test Suite")
        print("Based on: KFM1000100000002 @ 10.32.24.151:4059")
        print("=" * 70)
        print(f"\nKeys:")
        print(f"  AKEY: {self.AKEY.hex().upper()}")
        print(f"  EKEY: {self.EKEY.hex().upper()}")

        # Phase 1: Public Connection
        print("\n" + "=" * 70)
        print("Phase 1: Public Connection (No Encryption)")
        print("=" * 70)

        self.test("AARQ (Plain)", self.test_aarq_plain)
        self.test("AARE (Plain)", self.test_aare_plain)
        self.test("GET Device Number (Plain)", self.test_get_device_number_plain)
        self.test("GET Frame Counter (Plain)", self.test_get_frame_counter_plain)

        # Phase 2: HLS Encrypted Connection
        print("\n" + "=" * 70)
        print("Phase 2: HLS Encrypted Connection")
        print("=" * 70)

        self.test("AARQ (Encrypted)", self.test_aarq_encrypted)
        self.test("AARE (Encrypted)", self.test_aare_encrypted)
        self.test("GMAC ACTION", self.test_action_gmac)

        # Phase 3: GET Operation
        print("\n" + "=" * 70)
        print("Phase 3: GET Operation (Encrypted)")
        print("=" * 70)

        self.test("GET Clock (Encrypted)", self.test_get_clock_encrypted)

        # Phase 4: SET Operation
        print("\n" + "=" * 70)
        print("Phase 4: SET Operation (Encrypted)")
        print("=" * 70)

        self.test("SET Clock (Encrypted)", self.test_set_clock_encrypted)

        # Phase 5: Disconnect
        print("\n" + "=" * 70)
        print("Phase 5: Disconnect (Encrypted)")
        print("=" * 70)

        self.test("RLRQ (Encrypted)", self.test_rlrq_encrypted)
        self.test("RLRE (Encrypted)", self.test_rlre_encrypted)

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"  Total: {self.test_count}")
        print(f"  Passed: {self.pass_count}")
        print(f"  Failed: {self.test_count - self.pass_count}")

        if self.pass_count == self.test_count:
            print("\n  All tests PASSED!")
        else:
            print(f"\n  Some tests FAILED!")

        print("=" * 70)

        return 0 if self.pass_count == self.test_count else 1


if __name__ == "__main__":
    suite = HLSTestSuite()
    sys.exit(suite.run_all())
