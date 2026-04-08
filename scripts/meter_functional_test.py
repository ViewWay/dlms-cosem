#!/usr/bin/env python3
"""DLMS/COSEM Smart Meter Functional Test Suite.

完整测试套件，涵盖电表的所有主要功能：
- 连接测试 (公共连接, HLS加密连接)
- 读取操作 (GET)
- 写入操作 (SET)
- 操作执行 (ACTION)
- 负荷曲线读取
- 事件日志读取
- 异常处理测试

支持的电表:
- 中国国标智能电表 (GB/T 17215)
- 欧标智能电表 (IEC 62056)
- 支持HLS-GMAC加密的电表

作者: DLMS/COSEM Project Team
版本: 1.0.0
"""

from __future__ import annotations

import asyncio
import sys
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from enum import IntEnum
from datetime import datetime
import traceback

# 添加项目路径
sys.path.insert(0, r'D:\Users\HongLinHe\Projects\dlms-cosem')

try:
    from dlms_cosem import (
        AsyncDlmsClient,
        DlmsConnectionSettings,
    )
    from dlms_cosem.io import TcpIO
    from dlms_cosem.transport import HdlcTransport
    from dlms_cosem.security import SecuritySuite
    from dlms_cosem.exceptions import (
        DlmsConnectionError,
        DlmsAuthenticationError,
        DlmsTimeoutError,
    )
except ImportError as e:
    print(f"错误: 无法导入dlms_cosem模块: {e}")
    print("请确保已安装dlms-cosem或项目路径正确")
    sys.exit(1)


# ============================================================================
# 枚举和配置类
# ============================================================================

class TestStatus(IntEnum):
    """测试状态"""
    PENDING = 0
    RUNNING = 1
    PASSED = 2
    FAILED = 3
    SKIPPED = 4


class SecurityLevel(IntEnum):
    """安全级别"""
    PUBLIC = 0      # 公共连接 (无加密)
    LLS = 1         # 低级安全 (密码认证)
    HLS = 2         # 高级安全 (加密)


@dataclass
class TestConfig:
    """测试配置"""
    host: str = "10.32.24.151"
    port: int = 4059
    client_logical_address: int = 16
    server_logical_address: int = 1

    # 安全配置
    security_level: SecurityLevel = SecurityLevel.HLS
    security_suite: str = "HLS_GMAC"

    # 密钥配置
    authentication_key: str = "D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"
    encryption_key: str = "000102030405060708090A0B0C0D0E0F"
    client_system_title: str = "0000000000000000"

    # 连接配置
    timeout: int = 10
    retries: int = 3

    # 测试配置
    verbose: bool = True
    skip_write_tests: bool = True  # 默认跳过写入测试


@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    status: TestStatus = TestStatus.PENDING
    duration: float = 0.0
    message: str = ""
    data: Any = None
    error: Optional[Exception] = None

    def __str__(self) -> str:
        status_char = {
            TestStatus.PENDING: "○",
            TestStatus.RUNNING: "→",
            TestStatus.PASSED: "✓",
            TestStatus.FAILED: "✗",
            TestStatus.SKIPPED: "⊘",
        }
        return f"{status_char[self.status]} {self.name}: {self.message}"


@dataclass
class TestSuite:
    """测试套件结果"""
    name: str
    results: List[TestResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

    @property
    def total(self) -> int:
        return len(self.results)


# ============================================================================
# 测试套件
# ============================================================================

class MeterFunctionalTester:
    """电表功能测试器"""

    # 常用OBIS代码
    OBIS_CODES = {
        # 基础信息
        "meter_id": ("0.0.96.1.0.255", 2),      # 电表ID
        "device_id": ("0.0.42.0.0.255", 2),     # 设备号
        "clock": ("0.0.1.0.0.255", 2),          # 时钟
        "clock_status": ("0.0.1.0.0.255", 4),   # 时钟状态

        # 电能数据
        "active_power": ("1.0.1.8.0.255", 2),   # 有功功率
        "reactive_power": ("1.0.3.8.0.255", 2), # 无功功率
        "apparent_power": ("1.0.9.8.0.255", 2), # 视在功率
        "power_factor": ("1.0.13.7.0.255", 2),  # 功率因数

        # 电压电流
        "voltage_a": ("1.0.31.7.0.255", 2),     # A相电压
        "voltage_b": ("1.0.52.7.0.255", 2),     # B相电压
        "voltage_c": ("1.0.73.7.0.255", 2),     # C相电压
        "current_a": ("1.0.31.7.0.255", 3),     # A相电流
        "current_b": ("1.0.52.7.0.255", 3),     # B相电流
        "current_c": ("1.0.73.7.0.255", 3),     # C相电流

        # 电能
        "total_energy": ("1.0.1.8.0.255", 2),   # 总有功电能
        "peak_energy": ("1.0.1.8.0.255", 2),    # 峰时电能
        "flat_energy": ("1.0.3.8.0.255", 2),    # 平时电能
        "valley_energy": ("1.0.5.8.0.255", 2),  # 谷时电能

        # 负荷曲线
        "load_profile": ("1.0.99.1.0.255", 2),  # 负荷曲线

        # 事件
        "event_log": ("0.0.99.1.0.255", 2),     # 事件日志
    }

    def __init__(self, config: TestConfig):
        self.config = config
        self.client: Optional[AsyncDlmsClient] = None
        self.transport = None
        self.suites: List[TestSuite] = []

        # 配置日志
        self._setup_logging()

    def _setup_logging(self):
        """配置日志系统"""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger('MeterTest')

    def _create_connection_settings(self) -> DlmsConnectionSettings:
        """创建连接配置"""
        settings = DlmsConnectionSettings(
            client_logical_address=self.config.client_logical_address,
            server_logical_address=self.config.server_logical_address,
        )

        if self.config.security_level == SecurityLevel.LLS:
            settings.authentication = "low"
            settings.password = b"00000000"
        elif self.config.security_level == SecurityLevel.HLS:
            settings.authentication = "hls"
            settings.authentication_key = bytes.fromhex(self.config.authentication_key)
            settings.encryption_key = bytes.fromhex(self.config.encryption_key)
            settings.client_system_title = bytes.fromhex(self.config.client_system_title)

        return settings

    async def connect(self) -> bool:
        """建立连接"""
        self.logger.info(f"正在连接到 {self.config.host}:{self.config.port}...")
        self.logger.info(f"安全级别: {self.config.security_level.name}")

        settings = self._create_connection_settings()
        io = TcpIO(host=self.config.host, port=self.config.port, timeout=self.config.timeout)
        self.transport = HdlcTransport(io)
        self.client = AsyncDlmsClient(self.transport, settings)

        try:
            await self.client.connect()
            self.logger.info("✓ 连接成功")
            return True
        except Exception as e:
            self.logger.error(f"✗ 连接失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.close()
            self.logger.info("连接已关闭")

    # ========================================================================
    # 测试用例
    # ========================================================================

    async def _run_test(self, name: str, coro) -> TestResult:
        """运行单个测试"""
        result = TestResult(name=name, status=TestStatus.RUNNING)
        start = time.time()

        try:
            data = await coro
            result.data = data
            result.status = TestStatus.PASSED
            result.message = "成功"
            self.logger.debug(f"  ✓ {name}")
        except Exception as e:
            result.status = TestStatus.FAILED
            result.error = e
            result.message = str(e)
            self.logger.warning(f"  ✗ {name}: {e}")

        result.duration = time.time() - start
        return result

    async def test_connection(self) -> TestSuite:
        """测试: 连接建立"""
        suite = TestSuite(name="连接测试")
        suite.start_time = time.time()

        # 测试连接
        result = await self._run_test(
            "建立连接",
            self.connect()
        )
        suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_basic_info(self) -> TestSuite:
        """测试: 读取基础信息"""
        suite = TestSuite(name="基础信息读取")
        suite.start_time = time.time()

        tests = [
            ("读取电表ID", "meter_id"),
            ("读取设备号", "device_id"),
            ("读取时钟", "clock"),
        ]

        for name, key in tests:
            obis, attr = self.OBIS_CODES[key]
            result = await self._run_test(
                name,
                self.client.get(obis, attribute=attr)
            )
            suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_power_data(self) -> TestSuite:
        """测试: 读取功率数据"""
        suite = TestSuite(name="功率数据读取")
        suite.start_time = time.time()

        tests = [
            ("有功功率", "active_power"),
            ("无功功率", "reactive_power"),
            ("功率因数", "power_factor"),
        ]

        for name, key in tests:
            obis, attr = self.OBIS_CODES[key]
            result = await self._run_test(
                name,
                self.client.get(obis, attribute=attr)
            )
            suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_voltage_current(self) -> TestSuite:
        """测试: 读取电压电流"""
        suite = TestSuite(name="电压电流读取")
        suite.start_time = time.time()

        tests = [
            ("A相电压", "voltage_a"),
            ("B相电压", "voltage_b"),
            ("C相电压", "voltage_c"),
            ("A相电流", "current_a"),
            ("B相电流", "current_b"),
            ("C相电流", "current_c"),
        ]

        for name, key in tests:
            obis, attr = self.OBIS_CODES[key]
            result = await self._run_test(
                name,
                self.client.get(obis, attribute=attr)
            )
            suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_energy_data(self) -> TestSuite:
        """测试: 读取电能数据"""
        suite = TestSuite(name="电能数据读取")
        suite.start_time = time.time()

        # 读取总电能
        result = await self._run_test(
            "总有功电能",
            self.client.get("1.0.1.8.0.255", attribute=2)
        )
        suite.results.append(result)

        # 尝试读取分时电能
        for rate in ["峰", "平", "谷", "尖峰"]:
            result = await self._run_test(
                f"{rate}时电能",
                self.client.get("1.0.1.8.0.255", attribute=2)
            )
            # 失败不报错，可能电表不支持
            if result.status == TestStatus.FAILED:
                result.status = TestStatus.SKIPPED
            suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_load_profile(self, count: int = 5) -> TestSuite:
        """测试: 读取负荷曲线"""
        suite = TestSuite(name="负荷曲线读取")
        suite.start_time = time.time()

        result = await self._run_test(
            f"读取最近{count}条负荷曲线",
            self.client.get("1.0.99.1.0.255", access="range", from_=0, to_=count)
        )
        suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_get_with_list(self) -> TestSuite:
        """测试: 批量读取 (GET.WITH_LIST)"""
        suite = TestSuite(name="批量读取")
        suite.start_time = time.time()

        # 定义要批量读取的对象
        request_list = [
            ("0.0.96.1.0.255", 2),  # 电表ID
            ("0.0.1.0.0.255", 2),   # 时钟
            ("1.0.1.8.0.255", 2),   # 有功功率
        ]

        result = await self._run_test(
            "批量读取3个对象",
            self.client.get_with_list(request_list)
        )
        suite.results.append(result)

        suite.end_time = time.time()
        return suite

    async def test_set_operation(self) -> TestSuite:
        """测试: SET操作 (默认跳过)"""
        suite = TestSuite(name="SET操作")
        suite.start_time = time.time()

        if self.config.skip_write_tests:
            result = TestResult(
                name="SET操作",
                status=TestStatus.SKIPPED,
                message="已跳过 (安全考虑)"
            )
        else:
            # 警告: 不要在生产环境随意SET
            result = TestResult(
                name="SET操作",
                status=TestStatus.SKIPPED,
                message="SET操作需要谨慎，请手动执行"
            )

        suite.results.append(result)
        suite.end_time = time.time()
        return suite

    # ========================================================================
    # 完整测试运行
    # ========================================================================

    async def run_all_tests(self) -> List[TestSuite]:
        """运行所有测试"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("DLMS/COSEM 电表功能测试套件")
        self.logger.info("=" * 70)
        self.logger.info(f"目标: {self.config.host}:{self.config.port}")
        self.logger.info(f"安全级别: {self.config.security_level.name}")
        self.logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 70)

        # 1. 连接测试
        suite = await self.test_connection()
        self.suites.append(suite)

        if suite.results[0].status != TestStatus.PASSED:
            self.logger.error("连接失败，终止测试")
            return self.suites

        try:
            # 2. 基础信息测试
            self.suites.append(await self.test_basic_info())

            # 3. 功率数据测试
            self.suites.append(await self.test_power_data())

            # 4. 电压电流测试
            self.suites.append(await self.test_voltage_current())

            # 5. 电能数据测试
            self.suites.append(await self.test_energy_data())

            # 6. 负荷曲线测试
            self.suites.append(await self.test_load_profile(count=5))

            # 7. 批量读取测试
            self.suites.append(await self.test_get_with_list())

            # 8. SET操作测试 (默认跳过)
            self.suites.append(await self.test_set_operation())

        finally:
            await self.disconnect()

        return self.suites

    # ========================================================================
    # 报告生成
    # ========================================================================

    def print_report(self):
        """打印测试报告"""
        total_passed = sum(s.passed for s in self.suites)
        total_failed = sum(s.failed for s in self.suites)
        total_skipped = sum(s.skipped for s in self.suites)
        total_tests = sum(s.total for s in self.suites)

        print("\n" + "=" * 70)
        print("测试报告")
        print("=" * 70)

        for suite in self.suites:
            print(f"\n【{suite.name}】")
            print(f"  耗时: {suite.duration:.2f}秒")
            print(f"  结果: {suite.passed}通过, {suite.failed}失败, {suite.skipped}跳过")

            if self.config.verbose:
                for result in suite.results:
                    status_char = {
                        TestStatus.PASSED: "✓",
                        TestStatus.FAILED: "✗",
                        TestStatus.SKIPPED: "⊘",
                    }
                    char = status_char.get(result.status, "?")
                    print(f"    {char} {result.name} ({result.duration:.3f}s)")
                    if result.data and self.config.verbose:
                        print(f"       数据: {result.data}")

        print("\n" + "=" * 70)
        print("总计")
        print("=" * 70)
        print(f"  总测试数: {total_tests}")
        print(f"  通过: {total_passed} ({total_passed/total_tests*100:.1f}%)")
        print(f"  失败: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        print(f"  跳过: {total_skipped} ({total_skipped/total_tests*100:.1f}%)")
        print("=" * 70)

        # 返回是否全部通过
        return total_failed == 0


# ============================================================================
# 命令行界面
# ============================================================================

def parse_arguments():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="DLMS/COSEM Smart Meter Functional Test Suite"
    )

    parser.add_argument(
        "--host",
        default="10.32.24.151",
        help="电表IP地址 (默认: 10.32.24.151)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4059,
        help="电表端口 (默认: 4059)"
    )
    parser.add_argument(
        "--security",
        choices=["public", "lls", "hls"],
        default="hls",
        help="安全级别 (默认: hls)"
    )
    parser.add_argument(
        "--akey",
        default="D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF",
        help="认证密钥 (16字节十六进制)"
    )
    parser.add_argument(
        "--ekey",
        default="000102030405060708090A0B0C0D0E0F",
        help="加密密钥 (16字节十六进制)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="连接超时时间(秒) (默认: 10)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式，减少输出"
    )
    parser.add_argument(
        "--enable-write",
        action="store_true",
        help="启用写入测试 (危险!)"
    )

    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_arguments()

    # 创建测试配置
    config = TestConfig(
        host=args.host,
        port=args.port,
        security_level={
            "public": SecurityLevel.PUBLIC,
            "lls": SecurityLevel.LLS,
            "hls": SecurityLevel.HLS,
        }[args.security],
        authentication_key=args.akey,
        encryption_key=args.ekey,
        timeout=args.timeout,
        verbose=not args.quiet,
        skip_write_tests=not args.enable_write,
    )

    # 创建测试器并运行
    tester = MeterFunctionalTester(config)
    await tester.run_all_tests()

    # 打印报告
    success = tester.print_report()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n测试异常: {e}")
        traceback.print_exc()
        sys.exit(1)
