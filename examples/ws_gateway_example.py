"""Example: WebSocket Gateway for DLMS Meters

Starts a WebSocket gateway that bridges WebSocket clients to DLMS meters.
Requires: pip install websockets
"""
import asyncio
import json
from dlms_cosem.ws_gateway import WsGateway, DlmsProxy, GatewayConfig, ClientRole


async def dlms_command_handler(meter_id, command, params):
    """Simulated DLMS command handler."""
    print(f"DLMS Command: {command} on {meter_id} -> {params}")
    return {"simulated_value": 123.45}


async def main():
    proxy = DlmsProxy(dlms_command_handler)
    config = GatewayConfig(
        host="127.0.0.1",
        ws_port=8080,
        auth_token="my-secret-token",
    )
    gateway = WsGateway(proxy, config)

    # Add additional users
    gateway.auth.add_token("readonly-token", ClientRole.READONLY)
    gateway.auth.add_token("operator-token", ClientRole.OPERATOR)

    await gateway.start()
    print(f"WebSocket gateway running on ws://127.0.0.1:8080")
    print("Connect with token: 'my-secret-token' (admin)")

    try:
        # Simulate periodic data push
        for i in range(10):
            await asyncio.sleep(5)
            count = await gateway.push_data(
                "METER_001", "1.0.1.8.0.255", 100 + i * 0.1
            )
            if count > 0:
                print(f"Pushed data to {count} subscribed clients")
    except KeyboardInterrupt:
        pass
    finally:
        await gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())
