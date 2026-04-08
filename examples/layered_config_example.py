#!/usr/bin/env python3
"""DLMS/COSEM 分层配置使用示例

按照协议栈层次组织配置:
- Basic:   基础配置
- Key:     密钥配置
- HDLC:    数据链路层配置
- WPDU:    传输层配置 (TCP/IP)
- AARQ:    应用层配置 (认证/加密)
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dlms_cosem import AsyncDlmsClient
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport
from dlms_cosem.config.layered_config import (
    load_layered_config,
    BasicConfig,
    KeyConfig,
    HdlcConfig,
    WpduConfig,
    AarqConfig,
)


async def example_basic_usage():
    """基本使用示例"""
    print("\n" + "=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)

    # 加载配置
    config = load_layered_config(".env")

    # 获取默认电表配置
    meter_config = config.get_meter()

    print(f"\n电表配置 (meter_id={meter_config.meter_id}):")
    print(f"  [Basic]")
    print(f"    公共客户端ID: {meter_config.basic.public_client_id}")
    print(f"  [Key]")
    print(f"    AKEY: {meter_config.key.akey[:8]}...")
    print(f"    EKEY: {meter_config.key.ekey[:8]}...")
    print(f"  [HDLC]")
    print(f"    客户端地址: {meter_config.hdlc.client_logical_address}")
    print(f"    服务器地址: {meter_config.hdlc.server_logical_address}")
    print(f"  [WPDU]")
    print(f"    服务器IP: {meter_config.wpdu.server_ip}")
    print(f"    服务器端口: {meter_config.wpdu.server_port}")
    print(f"  [AARQ]")
    print(f"    认证机制: {meter_config.aarq.authentication_mechanism}")
    print(f"    访问级别: {meter_config.aarq.access_level}")


async def example_connect_meter():
    """连接电表示例"""
    print("\n" + "=" * 60)
    print("示例2: 连接电表")
    print("=" * 60)

    # 加载配置
    config = load_layered_config(".env")

    # 获取连接设置
    settings = config.to_connection_settings()
    host, port = config.get_host_port()

    print(f"\n连接参数:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  客户端地址: {settings.client_logical_address}")
    print(f"  服务器地址: {settings.server_logical_address}")
    print(f"  认证方式: {settings.authentication}")

    # 创建连接
    io = TcpIO(host=host, port=port)
    transport = HdlcTransport(io)
    client = AsyncDlmsClient(transport, settings)

    try:
        print(f"\n正在连接...")
        await client.connect()
        print(f"✓ 连接成功")

        # 读取电表ID
        meter_id = await client.get("0.0.96.1.0.255")
        print(f"  电表ID: {meter_id}")

        # 读取时钟
        clock = await client.get("0.0.1.0.0.255")
        print(f"  时钟: {clock}")

    except Exception as e:
        print(f"✗ 连接失败: {e}")
    finally:
        await client.close()


async def example_programmatic_config():
    """编程方式创建配置"""
    print("\n" + "=" * 60)
    print("示例3: 编程方式创建配置")
    print("=" * 60)

    from dlms_cosem.config.layered_config import MeterConfig

    # 创建配置
    meter_config = MeterConfig(
        meter_id="programmatic",
        basic=BasicConfig(
            public_client_id=16,
            frame_counter_mode="attribute",
        ),
        key=KeyConfig(
            akey="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
            ekey="000102030405060708090A0B0C0D0E0F",
        ),
        hdlc=HdlcConfig(
            client_logical_address=16,
            server_logical_address=1,
        ),
        wpdu=WpduConfig(
            server_ip="10.32.24.151",
            server_port=4059,
        ),
        aarq=AarqConfig(
            authentication_mechanism=2,  # HLS_GMAC
            access_level=2,
        ),
    )

    print(f"\n编程创建的配置:")
    print(f"  认证机制: {meter_config.aarq.authentication_mechanism} (HLS-GMAC)")
    print(f"  服务器: {meter_config.wpdu.server_ip}:{meter_config.wpdu.server_port}")
    print(f"  地址: {meter_config.hdlc.client_logical_address} -> {meter_config.hdlc.server_logical_address}")


async def example_list_meters():
    """列出所有配置的电表"""
    print("\n" + "=" * 60)
    print("示例4: 列出所有配置的电表")
    print("=" * 60)

    # 加载配置
    config = load_layered_config(".env")

    # 列出电表
    meters = config.list_meters()

    if meters:
        print(f"\n找到 {len(meters)} 个电表配置:")
        for meter_id in meters:
            meter_config = config.get_meter(meter_id)
            host, port = config.get_host_port(meter_id)
            print(f"  [{meter_id}] {host}:{port}")
    else:
        print("\n未找到电表特定配置，使用默认配置")
        meter_config = config.get_meter()
        print(f"  默认: {meter_config.wpdu.server_ip}:{meter_config.wpdu.server_port}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DLMS/COSEM 分层配置使用示例")
    print("=" * 60)

    print("\n协议栈层次:")
    print("  1. Basic   - 基础配置")
    print("  2. Key     - 密钥配置")
    print("  3. HDLC    - 数据链路层配置")
    print("  4. WPDU    - 传输层配置 (TCP/IP)")
    print("  5. AARQ    - 应用层配置 (认证/加密)")

    # 运行示例
    asyncio.run(example_basic_usage())
    asyncio.run(example_programmatic_config())
    asyncio.run(example_list_meters())

    # 取消注释以运行实际连接
    # asyncio.run(example_connect_meter())

    print("\n" + "=" * 60)
    print("提示: 取消注释 example_connect_meter() 以连接真实电表")
    print("=" * 60)


if __name__ == "__main__":
    main()
