#!/usr/bin/env python3
"""使用 .env 配置文件连接电表示例

本示例展示如何使用 .env 文件配置电表连接参数

步骤:
1. 复制 .env.example 为 .env
2. 修改 .env 文件中的电表参数
3. 运行此脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dlms_cosem import AsyncDlmsClient
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport
from dlms_cosem.config.env_config import (
    load_env,
    get_connection_settings,
    get_meter_host,
    list_meter_ids,
)


async def connect_default_meter():
    """使用默认配置连接电表"""
    print("\n" + "=" * 60)
    print("使用默认 .env 配置连接电表")
    print("=" * 60)

    # 加载 .env 文件
    load_env()

    # 获取连接设置
    settings = get_connection_settings()
    host, port = get_meter_host()

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

        # 读取有功功率
        power = await client.get("1.0.1.8.0.255")
        print(f"  有功功率: {power} W")

    except Exception as e:
        print(f"✗ 连接失败: {e}")
    finally:
        await client.close()


async def connect_specific_meter(meter_id: str):
    """连接指定电表"""
    print(f"\n{'=' * 60}")
    print(f"使用 .env 配置连接电表: {meter_id}")
    print("=" * 60)

    # 加载 .env 文件
    load_env()

    # 获取指定电表的连接设置
    settings = get_connection_settings(meter_id=meter_id)
    host, port = get_meter_host(meter_id=meter_id)

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

        # 读取数据
        meter_id_value = await client.get("0.0.96.1.0.255")
        print(f"  电表ID: {meter_id_value}")

    except Exception as e:
        print(f"✗ 连接失败: {e}")
    finally:
        await client.close()


async def connect_multiple_meters():
    """连接多个电表"""
    print("\n" + "=" * 60)
    print("使用 .env 配置连接多个电表")
    print("=" * 60)

    # 加载 .env 文件
    load_env()

    # 列出所有配置的电表
    meter_ids = list_meter_ids()

    if not meter_ids:
        print("  未找到配置的电表")
        print("  请在 .env 文件中配置 METER_001_HOST, METER_002_HOST 等")
        return

    print(f"\n找到 {len(meter_ids)} 个配置的电表: {meter_ids}")

    for meter_id in meter_ids:
        print(f"\n--- 连接电表 {meter_id} ---")

        try:
            settings = get_connection_settings(meter_id=meter_id)
            host, port = get_meter_host(meter_id=meter_id)

            io = TcpIO(host=host, port=port)
            transport = HdlcTransport(io)
            client = AsyncDlmsClient(transport, settings)

            await client.connect()
            meter_id_value = await client.get("0.0.96.1.0.255")
            print(f"  ✓ 电表ID: {meter_id_value}")

            await client.close()

        except Exception as e:
            print(f"  ✗ 连接失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(".env 配置文件使用示例")
    print("=" * 60)

    print("\n可用示例:")
    print("  1. 使用默认配置")
    print("  2. 连接指定电表")
    print("  3. 连接多个电表")
    print("  4. 列出所有配置的电表")

    # 加载 .env 并列出电表
    load_env()
    meter_ids = list_meter_ids()

    print(f"\n当前 .env 中配置的电表:")
    if meter_ids:
        for mid in meter_ids:
            settings = get_connection_settings(meter_id=mid)
            host, port = get_meter_host(meter_id=mid)
            print(f"  {mid}: {host}:{port} ({settings.authentication})")
    else:
        print(f"  默认配置")

    print("\n" + "=" * 60)
    print("运行示例:")
    print("=" * 60)
    print("\n# 使用默认配置")
    print("asyncio.run(connect_default_meter())")
    print("\n# 连接电表 001")
    print("asyncio.run(connect_specific_meter('001'))")
    print("\n# 连接所有配置的电表")
    print("asyncio.run(connect_multiple_meters())")

    # 取消注释以运行
    # asyncio.run(connect_default_meter())
    # asyncio.run(connect_specific_meter("001"))
    # asyncio.run(connect_multiple_meters())


if __name__ == "__main__":
    main()
