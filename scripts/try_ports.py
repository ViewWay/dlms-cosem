"""Test connection with different ports."""
import socket
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

METER_HOST = "10.32.24.151"
LLS_PASSWORD = b"\x00\x00\x00\x00\x00\x00\x00\x00"

# Try different ports
PORTS_TO_TRY = [4059, 4060, 6000, 8000, 8080, 9000, 10001, 10002, 22222]

print(f"Testing {METER_HOST} for DLMS connection...")
print("=" * 50)

working_port = None

for port in PORTS_TO_TRY:
    print(f"\nTrying port {port}...", end=" ")

    try:
        # Quick socket test
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((METER_HOST, port))
        sock.close()

        if result == 0:
            print("OPEN! Attempting DLMS connection...")
            working_port = port

            # Try actual DLMS connection
            try:
                from dlms_cosem import cosem, enumerations
                from dlms_cosem.client import DlmsClient
                from dlms_cosem.cosem import Obis
                from dlms_cosem.io import BlockingTcpIO, TcpTransport
                from dlms_cosem.security import LowLevelAuthentication

                tcp_io = BlockingTcpIO(host=METER_HOST, port=port, timeout=5)
                transport = TcpTransport(
                    client_logical_address=16,
                    server_logical_address=1,
                    io=tcp_io,
                )
                client = DlmsClient(
                    transport=transport,
                    authentication=LowLevelAuthentication(password=LLS_PASSWORD),
                )

                with client.session() as c:
                    attr = cosem.CosemAttribute(
                        interface=enumerations.CosemInterface.DATA,
                        instance=Obis.from_string("0.0.96.1.0.255"),
                        attribute=2,
                    )
                    data = c.get(attr)
                    print(f"SUCCESS! Got data: {data.hex()[:32]}...")
                    break

            except Exception as e:
                print(f"Port open but DLMS failed: {e}")
                # Try next port
                continue
        else:
            print("Closed")

    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 50)
if working_port:
    print(f"✓ Working port found: {working_port}")
else:
    print("✗ No working port found")
    print("\nYour meter may need:")
    print("  - Serial connection (RS-485 + optical head)")
    print("  - Check meter manual for correct port")
