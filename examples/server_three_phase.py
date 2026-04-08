"""Example: Simulated Three-Phase Meter COSEM Server

This example creates and starts a COSEM server that simulates a Chinese GB
three-phase smart meter, useful for testing DLMS client implementations.
"""
import asyncio
from dlms_cosem.server import create_three_phase_meter_server


async def main():
    server = create_three_phase_meter_server(
        host="127.0.0.1",
        port=4059,
        transport="tcp",
    )

    print("Three-phase meter server starting on 127.0.0.1:4059")
    print("COSEM objects loaded:")
    for key, obj in server.model.get_all_objects().items():
        ln = obj.logical_name
        val = getattr(obj, 'value', 'N/A')
        print(f"  {ln.a}.{ln.b}.{ln.c}.{ln.d}.{ln.e}.{ln.f} = {val}")

    await server.start()
    print("Server running. Press Ctrl+C to stop.")

    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()
        print("Server stopped.")


if __name__ == "__main__":
    asyncio.run(main())
