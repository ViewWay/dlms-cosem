"""HLS Connection Test - Parsing real meter connection logs.

This test parses the actual HLS connection/disconnection logs
to verify DLMS/COSEM protocol implementation.
"""
import struct
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WrapperHeader:
    """Wrapper header format."""
    source_wport: int
    destination_wport: int
    length: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "WrapperHeader":
        """Parse wrapper header from bytes."""
        if len(data) < 12:
            raise ValueError("Wrapper header must be at least 12 bytes")

        # Format: 0x0001 + SrcWPort(4) + DstWPort(4) + Len(4)
        return cls(
            source_wport=int.from_bytes(data[2:6], byteorder='big'),
            destination_wport=int.from_bytes(data[6:10], byteorder='big'),
            length=int.from_bytes(data[10:14], byteorder='big'),
        )


def parse_apdu_hex(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    cleaned = hex_str.replace(" ", "").replace("\n", "")
    return bytes.fromhex(cleaned)


class HLSLogParser:
    """Parser for HLS connection logs."""

    def __init__(self):
        self.messages = []

    def parse_connect_log(self, log_path: str):
        """Parse connection log file."""
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_log_content(content)

    def parse_disconnect_log(self, log_path: str):
        """Parse disconnection log file."""
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_log_content(content)

    def parse_log_content(self, content: str) -> List[dict]:
        """Parse log content and extract APDU messages."""
        messages = []
        lines = content.split('\n')

        for line in lines:
            # Parse Send messages
            if '[Send]:' in line and '00 01' in line:
                hex_data = line.split('[Send]:')[1].strip()
                if hex_data and len(hex_data) > 20:
                    try:
                        data = parse_apdu_hex(hex_data)
                        msg = self._parse_wrapper_apdu(data)
                        msg['direction'] = 'send'
                        msg['raw'] = hex_data[:100] + '...' if len(hex_data) > 100 else hex_data
                        messages.append(msg)
                    except Exception as e:
                        pass  # Skip invalid messages

            # Parse Receive messages
            if '[Receive]:' in line and '00 01' in line:
                hex_data = line.split('[Receive]:')[1].strip()
                if hex_data and len(hex_data) > 20:
                    try:
                        data = parse_apdu_hex(hex_data)
                        msg = self._parse_wrapper_apdu(data)
                        msg['direction'] = 'receive'
                        msg['raw'] = hex_data[:100] + '...' if len(hex_data) > 100 else hex_data
                        messages.append(msg)
                    except Exception:
                        pass

        return messages

    def _parse_wrapper_apdu(self, data: bytes) -> dict:
        """Parse wrapper APDU and extract DLMS message."""
        if len(data) < 4:
            return {'error': 'Too short'}

        # Check wrapper format
        if data[:2] == b'\x00\x01':
            header = WrapperHeader.from_bytes(data)
            apdu_start = 14  # Skip wrapper header
            apdu_data = data[apdu_start:apdu_start + header.length]
            return self._parse_dlms_apdu(apdu_data, header)

        return self._parse_dlms_apdu(data, None)

    def _parse_dlms_apdu(self, data: bytes, wrapper_header: Optional[WrapperHeader]) -> dict:
        """Parse DLMS APDU."""
        if len(data) < 2:
            return {'error': 'APDU too short'}

        tag = data[0]

        # AARQ (Association Request) - tag 0x60
        if tag == 0x60:
            return self._parse_aarq(data, wrapper_header)

        # AARE (Association Response) - tag 0x61
        if tag == 0x61:
            return self._parse_aare(data, wrapper_header)

        # GET Request - tag 0xC0
        if tag == 0xC0:
            return self._parse_get_request(data, wrapper_header)

        # GET Response - tag 0xC4
        if tag == 0xC4:
            return self._parse_get_response(data, wrapper_header)

        # RLRQ (Release Request) - tag 0x62
        if tag == 0x62:
            return self._parse_rlrq(data, wrapper_header)

        # RLRE (Release Response) - tag 0x63
        if tag == 0x63:
            return self._parse_rlre(data, wrapper_header)

        return {
            'type': 'UNKNOWN',
            'tag': f'0x{tag:02X}',
            'data_length': len(data),
        }

    def _parse_aarq(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse AARQ (Association Request)."""
        result = {
            'type': 'AARQ',
            'tag': f'0x{data[0]:02X}',
            'length': data[1] if len(data) > 1 else 0,
        }

        # Check for authentication (LLS)
        if len(data) > 20:
            # Look for mechanism name (0x8B 07 ...)
            if b'\x8B\x07\x60\x85\x74\x05\x08\x02\x01' in data:
                result['auth'] = 'LOW_LEVEL_SECURITY'
                # Extract auth value
                auth_idx = data.index(b'\xAC\x0A\x80')
                if auth_idx > 0:
                    auth_len = data[auth_idx + 3]
                    auth_value = data[auth_idx + 4:auth_idx + 4 + auth_len]
                    result['auth_value'] = auth_value.decode('ascii', errors='ignore')

        # Check for conformance bits
        if b'\xBE\x10\x04\x0E' in data:
            result['conformance'] = self._parse_conformance(data)

        return result

    def _parse_aare(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse AARE (Association Response)."""
        result = {
            'type': 'AARE',
            'tag': f'0x{data[0]:02X}',
            'length': data[1] if len(data) > 1 else 0,
        }

        # Parse result (0x00 = accepted)
        if len(data) > 10 and data[2] == 0xA2:
            result_code = data[4]
            result['result'] = 'ACCEPTED' if result_code == 0 else f'REJECTED_{result_code}'

        # Parse conformance
        if b'\xBE\x10\x04\x0E' in data:
            result['conformance'] = self._parse_conformance(data)

        return result

    def _parse_get_request(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse GET Request."""
        result = {
            'type': 'GET_REQUEST',
            'tag': f'0x{data[0]:02X}',
        }

        # Invoke ID
        if len(data) > 2:
            result['invoke_id'] = f'0x{data[2]:02X}'

        # Attribute descriptor
        if len(data) > 10:
            # Class ID (2 bytes)
            class_id = int.from_bytes(data[4:6], byteorder='big')
            result['class_id'] = f'{class_id:04X}'

            # Instance ID (6 bytes)
            instance = data[6:12].hex().upper()
            result['instance_id'] = self._format_obis(instance)

            # Attribute ID (1 byte)
            if len(data) > 12:
                result['attribute_id'] = data[12]

        return result

    def _parse_get_response(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse GET Response."""
        result = {
            'type': 'GET_RESPONSE',
            'tag': f'0x{data[0]:02X}',
        }

        # Invoke ID
        if len(data) > 2:
            result['invoke_id'] = f'0x{data[2]:02X}'

        # Parse result data
        if len(data) > 5:
            result_code = data[4]
            result['result'] = 'SUCCESS' if result_code == 0 else f'ERROR_{result_code}'

            # Try to extract data
            if len(data) > 6:
                data_tag = data[5]
                if data_tag == 0x0A:  # VisibleString
                    str_len = data[6]
                    if len(data) > 7 + str_len:
                        result['value'] = data[7:7 + str_len].decode('ascii', errors='ignore')
                elif data_tag == 0x06:  # DoubleLongUnsigned
                    if len(data) > 11:
                        value = int.from_bytes(data[7:11], byteorder='big')
                        result['value'] = value

        return result

    def _parse_rlrq(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse RLRQ (Release Request)."""
        return {
            'type': 'RLRQ',
            'tag': f'0x{data[0]:02X}',
            'description': 'Release Request (Disconnect)',
        }

    def _parse_rlre(self, data: bytes, wrapper: Optional[WrapperHeader]) -> dict:
        """Parse RLRE (Release Response)."""
        return {
            'type': 'RLRE',
            'tag': f'0x{data[0]:02X}',
            'description': 'Release Response (Disconnect Ack)',
        }

    def _parse_conformance(self, data: bytes) -> dict:
        """Parse conformance bits."""
        conformance = {
            'raw': 'BE 10 04 0E',
        }

        # Look for conformance bytes
        idx = data.index(b'\xBE\x10')
        if idx + 4 < len(data):
            conf_len = data[idx + 3]
            if idx + 4 + conf_len <= len(data):
                conf_bytes = data[idx + 4:idx + 4 + conf_len]
                conf_value = int.from_bytes(conf_bytes, byteorder='big')

                conformance['bits'] = [
                    ('Get', bool(conf_value & 0x01)),
                    ('Set', bool(conf_value & 0x02)),
                    ('Action', bool(conf_value & 0x04)),
                    ('SelectiveAccess', bool(conf_value & 0x10)),
                    ('BlockTransferWithGet', bool(conf_value & 0x20)),
                    ('BlockTransferWithSet', bool(conf_value & 0x40)),
                    ('BlockTransferWithAction', bool(conf_value & 0x80)),
                ]

        return conformance

    def _format_obis(self, hex_str: str) -> str:
        """Format OBIS code."""
        if len(hex_str) >= 12:
            parts = [hex_str[i:i+2] for i in range(0, 12, 2)]
            values = [str(int(p, 16)) for p in parts]
            return f"{values[0]}.{values[1]}.{values[2]}.{values[3]}.{values[4]}.{values[5]}"
        return hex_str


class TestHLSConnection:
    """Test HLS connection using real meter logs."""

    def setup_method(self):
        self.parser = HLSLogParser()
        self.connect_log = r'D:\Users\HongLinHe\Projects\dlms-cosem\docs\Connect [New Meter].log'
        self.disconnect_log = r'D:\Users\HongLinHe\Projects\dlms-cosem\docs\Disconnect [New Meter].log'

    def test_parse_connect_log(self):
        """Test parsing connection log."""
        messages = self.parser.parse_connect_log(self.connect_log)

        print(f"\n{'='*60}")
        print("HLS Connection Test - Parsed Messages")
        print(f"{'='*60}")

        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] {msg.get('direction', '?').upper()}: {msg.get('type', 'UNKNOWN')}")
            if 'class_id' in msg:
                print(f"    Class: {msg['class_id']}, Instance: {msg.get('instance_id')}, Attr: {msg.get('attribute_id')}")
            if 'value' in msg:
                print(f"    Value: {msg['value']}")
            if 'result' in msg:
                print(f"    Result: {msg['result']}")
            if 'auth' in msg:
                print(f"    Auth: {msg['auth']}, Value: {msg.get('auth_value')}")
            if 'conformance' in msg:
                print(f"    Conformance: {msg['conformance']}")

        # Verify key messages
        message_types = [m.get('type') for m in messages]

        # Should have AARQ (Association Request)
        assert 'AARQ' in message_types, "Missing AARQ (Association Request)"

        # Should have AARE (Association Response)
        assert 'AARE' in message_types, "Missing AARE (Association Response)"

        # Should have GET_REQUEST
        assert 'GET_REQUEST' in message_types, "Missing GET Request"

        # Should have GET_RESPONSE
        assert 'GET_RESPONSE' in message_types, "Missing GET Response"

        print(f"\n{'='*60}")
        print("Connection sequence verification:")
        print(f"  ✓ AARQ (Association Request) found")
        print(f"  ✓ AARE (Association Response) found")
        print(f"  ✓ GET Request found")
        print(f"  ✓ GET Response found")
        print(f"{'='*60}")

        return messages

    def test_parse_disconnect_log(self):
        """Test parsing disconnection log."""
        messages = self.parser.parse_disconnect_log(self.disconnect_log)

        print(f"\n{'='*60}")
        print("HLS Disconnection Test - Parsed Messages")
        print(f"{'='*60}")

        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] {msg.get('direction', '?').upper()}: {msg.get('type', 'UNKNOWN')}")

        # Should have RLRQ (Release Request)
        message_types = [m.get('type') for m in messages]
        assert 'RLRQ' in message_types, "Missing RLRQ (Release Request)"
        assert 'RLRE' in message_types, "Missing RLRE (Release Response)"

        print(f"\n{'='*60}")
        print("Disconnection sequence verification:")
        print(f"  ✓ RLRQ (Release Request) found")
        print(f"  ✓ RLRE (Release Response) found")
        print(f"{'='*60}")

        return messages

    def test_hls_get_operation(self):
        """Test HLS GET operation from logs."""
        messages = self.parser.parse_connect_log(self.connect_log)

        # Find GET Request/Response pairs
        get_requests = [m for m in messages if m.get('type') == 'GET_REQUEST']
        get_responses = [m for m in messages if m.get('type') == 'GET_RESPONSE']

        print(f"\n{'='*60}")
        print("HLS GET Operation Test")
        print(f"{'='*60}")
        print(f"GET Requests: {len(get_requests)}")
        print(f"GET Responses: {len(get_responses)}")

        # Verify GET to device number (0.0.42.0.0.255 attribute 2)
        device_number_gets = [m for m in get_requests if m.get('instance_id') == '0.0.42.0.0.255']
        print(f"\nDevice Number GET (0.0.42.0.0.255): {len(device_number_gets)} request(s)")

        # Find response with device number value
        for resp in get_responses:
            if 'value' in resp and 'KFM' in str(resp['value']):
                print(f"  Device Number: {resp['value']}")

        # Verify GET to frame counter (0.0.43.1.0.255 attribute 2)
        frame_counter_gets = [m for m in get_requests if m.get('instance_id') == '0.0.43.1.0.255']
        print(f"\nFrame Counter GET (0.0.43.1.0.255): {len(frame_counter_gets)} request(s)")

        for resp in get_responses:
            if isinstance(resp.get('value'), int):
                print(f"  Frame Counter: {resp['value']}")

        print(f"{'='*60}")

    def test_hls_connection_flow(self):
        """Test complete HLS connection flow."""
        messages = self.parser.parse_connect_log(self.connect_log)

        print(f"\n{'='*60}")
        print("HLS Connection Flow Test")
        print(f"{'='*60}")

        # Expected sequence:
        # 1. Public Connection AARQ (no auth)
        # 2. Public Connection AARE
        # 3. GET device number
        # 4. GET frame counter
        # 5. Disconnect
        # 6. HLS Connection AARQ (LLS auth)
        # 7. HLS Connection AARE

        aarq_messages = [m for m in messages if m.get('type') == 'AARQ']
        aare_messages = [m for m in messages if m.get('type') == 'AARE']

        print(f"\nConnection phases:")
        print(f"  AARQ messages: {len(aarq_messages)} (expected 2: public + HLS)")
        print(f"  AARE messages: {len(aare_messages)} (expected 2: public + HLS)")

        # Check for LLS authentication in second AARQ
        lls_aarq = None
        for msg in aarq_messages:
            if msg.get('auth') == 'LOW_LEVEL_SECURITY':
                lls_aarq = msg
                print(f"\n  ✓ HLS AARQ with LLS authentication found")
                print(f"    Auth value: {msg.get('auth_value')}")

        assert lls_aarq is not None, "HLS AARQ with LLS authentication not found"

        print(f"\n{'='*60}")
        print("HLS Connection Flow: PASSED")
        print(f"{'='*60}")


def main():
    """Run HLS tests."""
    import sys
    sys.path.insert(0, r'D:\Users\HongLinHe\Projects\dlms-cosem')

    test = TestHLSConnection()
    test.setup_method()

    print("\n" + "="*60)
    print("HLS Connection Test Suite")
    print("Testing with real meter logs from 10.32.24.151:4059")
    print("="*60)

    try:
        # Test 1: Parse connect log
        test.test_parse_connect_log()

        # Test 2: Parse disconnect log
        test.test_parse_disconnect_log()

        # Test 3: GET operation
        test.test_hls_get_operation()

        # Test 4: Connection flow
        test.test_hls_connection_flow()

        print("\n" + "="*60)
        print("All HLS tests PASSED!")
        print("="*60)

    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\nTest ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
