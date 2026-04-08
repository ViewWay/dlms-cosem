#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多项目实时抄表系统示例.

支持:
  - 多项目管理
  - 不同加密级别 (LLS/HLS/证书)
  - 实时抄表
  - WebSocket推送
  - REST API

运行方式:
    python examples/multi_project_amr_system.py
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from enum import IntEnum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dlms_cosem import AsyncDlmsClient, DlmsConnectionSettings
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport
from dlms_cosem.config import load_layered_config


# ============================================================================
# 枚举定义
# ============================================================================

class SecurityLevel(IntEnum):
    """安全级别"""
    PUBLIC = 0      # 无加密
    LLS = 1         # 低级安全 (密码)
    HLS_GMAC = 2    # 高级安全 (HLS-GMAC)
    HLS_CERT = 3    # 证书认证


class MeterStatus(IntEnum):
    """电表状态"""
    ONLINE = 1
    OFFLINE = 2
    ERROR = 3
    READING = 4


class ReadMode(IntEnum):
    """抄读模式"""
    REALTIME = 1     # 实时抄读
    SCHEDULED = 2    # 定时抄读
    ON_DEMAND = 3    # 按需抄读


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class MeterConfig:
    """电表配置"""
    meter_id: str                    # 电表唯一标识
    project_id: str                  # 所属项目
    name: str                        # 电表名称
    host: str                        # IP地址
    port: int                        # 端口

    # 地址配置
    client_address: int = 16         # 客户端地址
    server_address: int = 1          # 服务器地址

    # 安全配置
    security_level: SecurityLevel = SecurityLevel.LLS
    password: str = "00000000"       # LLS密码

    # HLS配置
    akey: str = ""                   # 认证密钥
    ekey: str = ""                   # 加密密钥
    client_system_title: str = "0000000000000000"

    # 超时配置
    timeout: int = 10
    retry: int = 3

    # 抄读配置
    read_interval: int = 300         # 抄读间隔(秒)
    enabled: bool = True             # 是否启用

    # 证书配置 (如果使用证书认证)
    cert_path: str = ""
    key_path: str = ""


@dataclass
class MeterData:
    """电表数据"""
    meter_id: str
    project_id: str
    timestamp: datetime
    data: Dict[str, Any]

    # 常见读数
    voltage: Optional[float] = None     # 电压 (V)
    current: Optional[float] = None     # 电流 (A)
    active_power: Optional[float] = None  # 有功功率 (W)
    reactive_power: Optional[float] = None # 无功功率 (var)
    power_factor: Optional[float] = None   # 功率因数
    total_energy: Optional[float] = None   # 总电能 (kWh)

    # 状态
    status: MeterStatus = MeterStatus.ONLINE
    error_message: str = ""


@dataclass
class ProjectConfig:
    """项目配置"""
    project_id: str
    project_name: str
    security_level: SecurityLevel = SecurityLevel.LLS

    # 默认密钥配置 (可被电表配置覆盖)
    default_password: str = "00000000"
    default_akey: str = ""
    default_ekey: str = ""
    default_client_title: str = "0000000000000000"

    # 实时抄读配置
    realtime_enabled: bool = True
    max_concurrent_reads: int = 10


# ============================================================================
# 抄表系统核心
# ============================================================================

class MeterConnectionPool:
    """电表连接池"""

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._connections: Dict[str, AsyncDlmsClient] = {}
        self._in_use: set = set()

    async def get_connection(self, config: MeterConfig) -> AsyncDlmsClient:
        """获取连接"""
        meter_id = config.meter_id

        # 如果已有连接且未被使用，直接返回
        if meter_id in self._connections and meter_id not in self._in_use:
            self._in_use.add(meter_id)
            return self._connections[meter_id]

        # 创建新连接
        client = await self._create_connection(config)
        self._connections[meter_id] = client
        self._in_use.add(meter_id)

        return client

    async def release_connection(self, meter_id: str):
        """释放连接"""
        if meter_id in self._in_use:
            self._in_use.remove(meter_id)

    async def _create_connection(self, config: MeterConfig) -> AsyncDlmsClient:
        """创建连接"""
        # 创建IO
        io = TcpIO(host=config.host, port=config.port, timeout=config.timeout)
        transport = HdlcTransport(io)

        # 创建连接设置
        settings = DlmsConnectionSettings(
            client_logical_address=config.client_address,
            server_logical_address=config.server_address,
        )

        # 配置安全
        if config.security_level == SecurityLevel.PUBLIC:
            settings.authentication = "none"
        elif config.security_level == SecurityLevel.LLS:
            settings.authentication = "low"
            settings.password = config.password.encode("ascii")
        elif config.security_level == SecurityLevel.HLS_GMAC:
            settings.authentication = "hls"
            if config.akey:
                settings.authentication_key = bytes.fromhex(config.akey)
            if config.ekey:
                settings.encryption_key = bytes.fromhex(config.ekey)
            settings.client_system_title = bytes.fromhex(config.client_system_title)
        elif config.security_level == SecurityLevel.HLS_CERT:
            settings.authentication = "hls"
            # 证书认证配置
            # 这里需要根据实际证书配置调整
            if config.akey:
                settings.authentication_key = bytes.fromhex(config.akey)
            if config.ekey:
                settings.encryption_key = bytes.fromhex(config.ekey)

        # 创建客户端
        client = AsyncDlmsClient(transport, settings)

        # 连接
        await client.connect()

        return client

    async def close_all(self):
        """关闭所有连接"""
        for meter_id, client in self._connections.items():
            try:
                await client.close()
            except Exception:
                pass
        self._connections.clear()
        self._in_use.clear()


class MultiProjectMeterSystem:
    """多项目抄表系统"""

    def __init__(self):
        self.projects: Dict[str, ProjectConfig] = {}
        self.meters: Dict[str, MeterConfig] = {}  # meter_id -> config
        self.connection_pool = MeterConnectionPool(max_size=20)

        # 数据回调
        self.data_callbacks: List[callable] = []

        # 实时抄读任务
        self._read_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        # 日志
        self.logger = logging.getLogger(__name__)

    def add_project(self, project: ProjectConfig):
        """添加项目"""
        self.projects[project.project_id] = project
        self.logger.info(f"添加项目: {project.project_name} ({project.project_id})")

    def add_meter(self, meter: MeterConfig):
        """添加电表"""
        self.meters[meter.meter_id] = meter
        self.logger.info(f"添加电表: {meter.name} ({meter.meter_id}) "
                        f"项目: {meter.project_id} 安全: {meter.security_level.name}")

    def add_data_callback(self, callback: callable):
        """添加数据回调"""
        self.data_callbacks.append(callback)

    async def read_meter(self, meter_id: str) -> MeterData:
        """读取单个电表数据"""
        if meter_id not in self.meters:
            raise ValueError(f"电表不存在: {meter_id}")

        config = self.meters[meter_id]

        try:
            # 获取连接
            client = await self.connection_pool.get_connection(config)

            # 读取数据
            data = await self._read_meter_data(client, config)

            # 释放连接
            await self.connection_pool.release_connection(meter_id)

            return data

        except Exception as e:
            self.logger.error(f"读取电表 {meter_id} 失败: {e}")
            return MeterData(
                meter_id=meter_id,
                project_id=config.project_id,
                timestamp=datetime.now(),
                data={},
                status=MeterStatus.ERROR,
                error_message=str(e),
            )

    async def _read_meter_data(self, client: AsyncDlmsClient,
                               config: MeterConfig) -> MeterData:
        """读取电表数据 (内部方法)"""

        # 常用OBIS代码
        obis_codes = {
            "voltage": "1.0.31.7.0.255",      # 电压
            "current": "1.0.31.7.0.255",      # 电流 (属性3)
            "active_power": "1.0.1.8.0.255",   # 有功功率
            "reactive_power": "1.0.3.8.0.255", # 无功功率
            "power_factor": "1.0.13.7.0.255",  # 功率因数
            "total_energy": "1.0.1.8.0.255",   # 总电能 (正向有功)
        }

        data = {}

        # 读取各项数据
        try:
            # 读取电压
            data["voltage"] = await client.get(obis_codes["voltage"], attribute=2)
        except Exception:
            data["voltage"] = None

        try:
            # 读取电流
            data["current"] = await client.get(obis_codes["current"], attribute=3)
        except Exception:
            data["current"] = None

        try:
            # 读取有功功率
            data["active_power"] = await client.get(obis_codes["active_power"], attribute=2)
        except Exception:
            data["active_power"] = None

        try:
            # 读取无功功率
            data["reactive_power"] = await client.get(obis_codes["reactive_power"], attribute=2)
        except Exception:
            data["reactive_power"] = None

        try:
            # 读取功率因数
            data["power_factor"] = await client.get(obis_codes["power_factor"], attribute=2)
        except Exception:
            data["power_factor"] = None

        try:
            # 读取总电能
            data["total_energy"] = await client.get(obis_codes["total_energy"], attribute=2)
        except Exception:
            data["total_energy"] = None

        # 构造返回数据
        return MeterData(
            meter_id=config.meter_id,
            project_id=config.project_id,
            timestamp=datetime.now(),
            data=data,
            voltage=data.get("voltage"),
            current=data.get("current"),
            active_power=data.get("active_power"),
            reactive_power=data.get("reactive_power"),
            power_factor=data.get("power_factor"),
            total_energy=data.get("total_energy"),
            status=MeterStatus.ONLINE,
        )

    async def read_project_meters(self, project_id: str,
                                  realtime: bool = False) -> List[MeterData]:
        """读取项目所有电表"""
        # 获取项目下的所有电表
        project_meters = [
            m for m in self.meters.values()
            if m.project_id == project_id and m.enabled
        ]

        if not realtime:
            # 普通抄读，顺序执行
            results = []
            for meter in project_meters:
                data = await self.read_meter(meter.meter_id)
                results.append(data)
            return results
        else:
            # 实时抄读，并发执行
            tasks = [self.read_meter(m.meter_id) for meter in project_meters]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤异常结果
            return [r for r in results if isinstance(r, MeterData)]

    async def read_all_meters(self, realtime: bool = False) -> Dict[str, List[MeterData]]:
        """读取所有项目电表"""
        results = {}

        for project_id in self.projects:
            results[project_id] = await self.read_project_meters(project_id, realtime)

        return results

    async def start_realtime_reading(self):
        """启动实时抄读"""
        if self._running:
            return

        self._running = True

        # 为每个启用的电表启动实时抄读任务
        for meter_id, config in self.meters.items():
            if config.enabled:
                task = asyncio.create_task(self._realtime_read_loop(meter_id))
                self._read_tasks[meter_id] = task

        self.logger.info(f"启动实时抄读，共 {len(self._read_tasks)} 个电表")

    async def _realtime_read_loop(self, meter_id: str):
        """实时抄读循环"""
        config = self.meters[meter_id]

        while self._running:
            try:
                # 读取数据
                data = await self.read_meter(meter_id)

                # 触发回调
                for callback in self.data_callbacks:
                    try:
                        await callback(data)
                    except Exception as e:
                        self.logger.error(f"数据回调失败: {e}")

                # 等待下次抄读
                await asyncio.sleep(config.read_interval)

            except Exception as e:
                self.logger.error(f"实时抄读 {meter_id} 失败: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟

    async def stop_realtime_reading(self):
        """停止实时抄读"""
        self._running = False

        # 取消所有任务
        for task in self._read_tasks.values():
            task.cancel()

        # 等待任务结束
        await asyncio.gather(*self._read_tasks.values(), return_exceptions=True)

        self._read_tasks.clear()
        self.logger.info("停止实时抄读")

    async def close(self):
        """关闭系统"""
        await self.stop_realtime_reading()
        await self.connection_pool.close_all()


# ============================================================================
# 示例配置
# ============================================================================

def create_example_system() -> MultiProjectMeterSystem:
    """创建示例抄表系统"""

    system = MultiProjectMeterSystem()

    # 项目1: 普通居民电表 (低安全)
    project1 = ProjectConfig(
        project_id="project_residential",
        project_name="居民小区项目",
        security_level=SecurityLevel.LLS,
        default_password="00000000",
        realtime_enabled=True,
        max_concurrent_reads=20,
    )
    system.add_project(project1)

    # 项目2: 商业电表 (高加密)
    project2 = ProjectConfig(
        project_id="project_commercial",
        project_name="商业综合体",
        security_level=SecurityLevel.HLS_GMAC,
        default_akey="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
        default_ekey="000102030405060708090A0B0C0D0E0F",
        realtime_enabled=True,
        max_concurrent_reads=10,
    )
    system.add_project(project2)

    # 项目3: 工业电表 (证书认证)
    project3 = ProjectConfig(
        project_id="project_industrial",
        project_name="工业园区",
        security_level=SecurityLevel.HLS_CERT,
        default_akey="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
        default_ekey="000102030405060708090A0B0C0D0E0F",
        realtime_enabled=True,
        max_concurrent_reads=5,
    )
    system.add_project(project3)

    # 添加居民电表 (低加密)
    for i in range(1, 11):
        meter = MeterConfig(
            meter_id=f"RES_{i:04d}",
            project_id="project_residential",
            name=f"居民电表 {i}号",
            host=f"10.32.24.{150+i}",
            port=4059,
            security_level=SecurityLevel.LLS,
            password="00000000",
            read_interval=300,  # 5分钟
        )
        system.add_meter(meter)

    # 添加商业电表 (高加密)
    for i in range(1, 6):
        meter = MeterConfig(
            meter_id=f"COM_{i:04d}",
            project_id="project_commercial",
            name=f"商业电表 {i}号",
            host=f"10.32.25.{150+i}",
            port=4059,
            security_level=SecurityLevel.HLS_GMAC,
            akey="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
            ekey="000102030405060708090A0B0C0D0E0F",
            read_interval=60,  # 1分钟
        )
        system.add_meter(meter)

    # 添加工业电表 (证书认证)
    for i in range(1, 4):
        meter = MeterConfig(
            meter_id=f"IND_{i:04d}",
            project_id="project_industrial",
            name=f"工业电表 {i}号",
            host=f"10.32.26.{150+i}",
            port=4059,
            security_level=SecurityLevel.HLS_CERT,
            akey="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
            ekey="000102030405060708090A0B0C0D0E0F",
            read_interval=30,  # 30秒
        )
        system.add_meter(meter)

    return system


# ============================================================================
# WebSocket 实时推送服务器
# ============================================================================

class RealtimeDataPusher:
    """实时数据推送服务"""

    def __init__(self, system: MultiProjectMeterSystem):
        self.system = system
        self._clients = set()

    async def handle_client(self, websocket, project_id: Optional[str] = None):
        """处理WebSocket客户端"""
        self._clients.add(websocket)

        try:
            # 发送历史数据
            await self._send_history(websocket, project_id)

            # 保持连接，推送新数据
            async for data in self._data_stream(project_id):
                await websocket.send_json(data.to_dict())

        finally:
            self._clients.remove(websocket)

    async def _send_history(self, websocket, project_id: Optional[str]):
        """发送历史数据"""
        # 这里可以从数据库读取历史数据
        pass

    async def _data_stream(self, project_id: Optional[str]):
        """数据流"""
        queue = asyncio.Queue()

        def callback(data: MeterData):
            if project_id is None or data.project_id == project_id:
                queue.put_nowait(data)

        self.system.add_data_callback(callback)

        while True:
            data = await queue.get()
            yield data

    def add_data_callback(self, callback: callable):
        """添加数据回调"""
        self.system.add_data_callback(callback)


# ============================================================================
# 主程序
# ============================================================================

async def main():
    """主程序"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 70)
    print("多项目实时抄表示例")
    print("=" * 70)

    # 创建系统
    system = create_example_system()

    # 添加数据回调
    def data_callback(data: MeterData):
        print(f"[{data.timestamp.strftime('%H:%M:%S')}] "
              f"{data.meter_id} | "
              f"电压: {data.voltage}V | "
              f"功率: {data.active_power}W | "
              f"状态: {data.status.name}")

    system.add_data_callback(lambda d: asyncio.create_task(data_callback(d)))

    # 实时读取单个项目
    print("\n读取商业项目电表 (实时模式):")
    results = await system.read_project_meters("project_commercial", realtime=True)

    for data in results:
        if data.status == MeterStatus.ONLINE:
            print(f"  {data.meter_id}: 功率={data.active_power}W 电压={data.voltage}V")
        else:
            print(f"  {data.meter_id}: ERROR - {data.error_message}")

    print(f"\n成功读取 {len([r for r in results if r.status == MeterStatus.ONLINE])} 个电表")

    # 关闭系统
    await system.close()


if __name__ == "__main__":
    asyncio.run(main())
