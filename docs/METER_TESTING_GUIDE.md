# DLMS/COSEM 电表功能测试完整指南

## 目录

1. [快速开始](#快速开始)
2. [库的安装](#库的安装)
3. [连接电表](#连接电表)
4. [基础读取操作](#基础读取操作)
5. [高级测试功能](#高级测试功能)
6. [完整测试示例](#完整测试示例)
7. [常见问题](#常见问题)

---

## 快速开始

### 最简单的连接测试

```python
from dlms_cosem.io import BlockingTcpIO, TcpTransport
from dlms_cosem.client import DlmsClient
from dlms_cosem.security import LowLevelAuthentication
from dlms_cosem.cosem import Obis, enumerations

# 创建 TCP IO
tcp_io = BlockingTcpIO(
    host="10.32.24.151",
    port=4059,
    timeout=10
)

# 创建传输层
transport = TcpTransport(
    client_logical_address=1,
    server_logical_address=1,
    io=tcp_io,
)

# 创建客户端 (LLS 认证)
client = DlmsClient(
    transport=transport,
    authentication=LowLevelAuthentication(password=b"\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"),
)

# 连接并读取数据
with client.session() as c:
    # 读取帧计数器
    attr = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=Obis.from_string("0.0.43.1.0.255"),
        attribute=2,
    )
    data = c.get(attr)
    print(f"Frame Counter: {data.hex()}")
```

---

## 库的安装

### 1. 从源码安装

```bash
cd D:\\Users\\HongLinHe\\Projects\\dlms-cosem
pip install -e .
```

### 2. 安装依赖

```bash
pip install cryptography pyserial
```

---

## 连接电表

### 认证方式对比

| 认证方式 | 适用场景 | 密码长度 |
|----------|----------|----------|
| NoSecurity | 公开客户端 | 无 |
| LLS | 低级安全 | 8 字节 |
| HLS | 高级安全 | 16 字节 |

### 连接配置

```python
from dlms_cosem.io import BlockingTcpIO, TcpTransport
from dlms_cosem.security import (
    NoSecurityAuthentication,
    LowLevelAuthentication,
    HighLevelSecurityGmacAuthentication,
)

# TCP 连接配置
tcp_io = BlockingTcpIO(
    host="10.32.24.151",  # 电表 IP
    port=4059,             # DLMS 端口
    timeout=10,             # 超时时间(秒)
)

# 传输层配置
transport = TcpTransport(
    client_logical_address=1,   # 客户端逻辑地址 (1=管理)
    server_logical_address=1,   # 服务器逻辑地址
    io=tcp_io,
)

# 选择认证方式
authentications = {
    "无认证": NoSecurityAuthentication(),
    "LLS": LowLevelAuthentication(password=b"\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"),
    "HLS": HighLevelSecurityGmacAuthentication(challenge_length=32),
}
```

---

## 基础读取操作

### 1. 读取单个属性

```python
with client.session() as c:
    # 方法1: 使用 CosemAttribute
    attr = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=Obis.from_string("0.0.43.1.0.255"),
        attribute=2,
    )
    data = c.get(attr)

    # 方法2: 直接使用 get_with_range (Profile Generic)
    profile_data = c.get_with_range(
        cosem_attribute=cosem.CosemAttribute(
            interface=enumerations.CosemInterface.PROFILE_GENERIC,
            instance=Obis.from_string("1.0.99.1.0.255"),
            attribute=2,
        ),
        from_value=datetime(2024, 1, 1),
        to_value=datetime(2024, 1, 31, 23, 59, 59),
    )
```

### 2. 常用 OBIS 代码

| 功能 | OBIS 代码 | 接口 | 属性 |
|------|-----------|------|------|
| 帧计数器 | 0.0.43.1.0.255 | DATA | 2 |
| 电表 ID | 0.0.42.0.0.255 | DATA | 2 |
| 时钟 | 0.0.1.0.0.255 | CLOCK | 2 |
| 有功功率+ | 1.0.1.8.0.255 | REGISTER | 2 |
| 电压 | 1.0.31.7.0.255 | REGISTER | 2 |
| 电流 | 1.0.51.5.0.255 | REGISTER | 2 |
| 功率因数 | 1.0.61.7.0.255 | REGISTER | 2 |

### 3. 数据解析

```python
from dlms_cosem import a_xdr

# 解析 Double Long Unsigned (无符号32位整数)
decoder = a_xdr.AXdrDecoder(
    encoding_conf=a_xdr.EncodingConf([
        a_xdr.DoubleLongUnsigned(attribute_name="value")
    ])
)
result = decoder.decode(data)
print(f"Value: {result['value']}")

# 解析 Octet String (字符串)
decoder = a_xdr.AXdrDecoder(
    encoding_conf=a_xdr.EncodingConf([
        a_xdr.OctetString(attribute_name="text")
    ])
)
result = decoder.decode(data)
print(f"Text: {result['text']}")
```

---

## 高级测试功能

### 1. 批量读取

```python
def read_multiple_attributes(client):
    """批量读取多个属性"""
    attributes = [
        ("帧计数器", "0.0.43.1.0.255", enumerations.CosemInterface.DATA, 2),
        ("时钟", "0.0.1.0.0.255", enumerations.CosemInterface.CLOCK, 2),
        ("有功功率", "1.0.1.8.0.255", enumerations.CosemInterface.REGISTER, 2),
    ]

    with client.session() as c:
        for name, obis, interface, attr_id in attributes:
            try:
                attr = cosem.CosemAttribute(
                    interface=interface,
                    instance=Obis.from_string(obis),
                    attribute=attr_id,
                )
                data = c.get(attr)
                print(f"{name}: {data.hex()}")
            except Exception as e:
                print(f"{name}: 失败 - {e}")
```

### 2. 定时读取 (模拟抄表)

```python
import time

def scheduled_reading(client, interval_seconds=60):
    """定时读取数据"""
    with client.session() as c:
        while True:
            try:
                # 读取当前总功率
                attr = cosem.CosemAttribute(
                    interface=enumerations.CosemInterface.REGISTER,
                    instance=Obis.from_string("1.0.1.8.0.255"),
                    attribute=2,
                )
                data = c.get(attr)

                # 解析值
                decoder = a_xdr.AXdrDecoder(
                    encoding_conf=a_xdr.EncodingConf([
                        a_xdr.DoubleLongUnsigned(attribute_name="power")
                    ])
                )
                result = decoder.decode(data)
                power = result.get("power", 0) / 100  # 转换为 kW

                print(f"[{time.strftime('%H:%M:%S')}] 功率: {power:.2f} kW")

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] 读取失败: {e}")

            time.sleep(interval_seconds)
```

### 3. 连接稳定性测试

```python
def test_connection_stability(client, num_reads=100):
    """测试连接稳定性"""
    results = []

    with client.session() as c:
        attr = cosem.CosemAttribute(
            interface=enumerations.CosemInterface.DATA,
            instance=Obis.from_string("0.0.43.1.0.255"),
            attribute=2,
        )

        for i in range(num_reads):
            try:
                start = time.time()
                data = c.get(attr)
                elapsed = time.time() - start

                results.append({
                    'index': i,
                    'success': True,
                    'time': elapsed,
                    'data': data.hex()[:20],
                })
                print(f"[{i+1}/{num_reads}] OK ({elapsed:.3f}s)")

            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e),
                })
                print(f"[{i+1}/{num_reads}] FAILED: {e}")

    # 统计
    success_count = sum(1 for r in results if r['success'])
    avg_time = sum(r['time'] for r in results if r['success'] / success_count if success_count > 0 else 0)

    print(f"\n成功率: {success_count}/{num_reads}")
    print(f"平均响应时间: {avg_time:.3f}s")

    return results
```

### 4. 错误处理

```python
from dlms_cosem import exceptions

def safe_read_with_retry(client, obis_str, max_retries=3):
    """带重试的安全读取"""
    attr = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=Obis.from_string(obis_str),
        attribute=2,
    )

    for attempt in range(max_retries):
        try:
            with client.session() as c:
                data = c.get(attr)
                return data, None
        except exceptions.CommunicationError as e:
            print(f"通信错误 (重试 {attempt+1}/{max_retries}): {e}")
            time.sleep(1)
        except exceptions.DlmsSecurityError as e:
            print(f"安全错误: {e}")
            return None, str(e)
        except Exception as e:
            print(f"未知错误: {e}")
            return None, str(e)

    return None, "Max retries exceeded"
```

---

## 完整测试示例

### 示例 1: 基础电表信息读取

```python
# scripts/read_meter_basic.py
import logging
from dlms_cosem import cosem, enumerations
from dlms_cosem.client import DlmsClient
from dlms_cosem.io import BlockingTcpIO, TcpTransport
from dlms_cosem.security import LowLevelAuthentication
from dlms_cosem.cosem import Obis

logging.basicConfig(level=logging.INFO, format='%(message)s')

def read_meter_basic(host="10.32.24.151", port=4059):
    """读取电表基本信息"""

    # 创建客户端
    tcp_io = BlockingTcpIO(host=host, port=port, timeout=10)
    transport = TcpTransport(
        client_logical_address=1,
        server_logical_address=1,
        io=tcp_io,
    )
    client = DlmsClient(
        transport=transport,
        authentication=LowLevelAuthentication(password=b"\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"),
    )

    # 测试项
    tests = [
        ("帧计数器", "0.0.43.1.0.255", enumerations.CosemInterface.DATA, 2),
        ("时钟", "0.0.1.0.0.255", enumerations.CosemInterface.CLOCK, 2),
        ("有功功率", "1.0.1.8.0.255", enumerations.CosemInterface.REGISTER, 2),
    ]

    with client.session() as c:
        for name, obis, interface, attr_id in tests:
            try:
                attr = cosem.CosemAttribute(
                    interface=interface,
                    instance=Obis.from_string(obis),
                    attribute=attr_id,
                )
                data = c.get(attr)
                logging.info(f"{name}: {data.hex()}")
            except Exception as e:
                logging.error(f"{name}: 失败 - {e}")

if __name__ == "__main__":
    read_meter_basic()
```

### 示例 2: 完整的测试套件

```python
# scripts/full_meter_test.py
import sys
import time
from datetime import datetime
from dlms_cosem import cosem, enumerations, a_xdr
from dlms_cosem.client import DlmsClient
from dlms_cosem.io import BlockingTcpIO, TcpTransport
from dlms_cosem.security import LowLevelAuthentication
from dlms_cosem.cosem import Obis

class MeterTester:
    """电表功能测试器"""

    def __init__(self, host, port=4059, password="00000000"):
        self.host = host
        self.port = port
        self.password = password
        self.results = []

    def create_client(self):
        """创建 DLMS 客户端"""
        tcp_io = BlockingTcpIO(
            host=self.host,
            port=self.port,
            timeout=10,
        )
        transport = TcpTransport(
            client_logical_address=1,
            server_logical_address=1,
            io=tcp_io,
        )
        return DlmsClient(
            transport=transport,
            authentication=LowLevelAuthentication(
                password=self.password.encode('ascii')
            ),
        )

    def test_connection(self):
        """测试连接"""
        print("\n[测试] 连接测试")
        try:
            client = self.create_client()
            with client.session() as c:
                # 尝试读取帧计数器
                attr = cosem.CosemAttribute(
                    interface=enumerations.CosemInterface.DATA,
                    instance=Obis.from_string("0.0.43.1.0.255"),
                    attribute=2,
                )
                data = c.get(attr)
                print(f"  ✓ 连接成功，帧计数器: {data.hex()}")
                return True
        except Exception as e:
            print(f"  ✗ 连接失败: {e}")
            return False

    def test_read_registers(self):
        """测试寄存器读取"""
        print("\n[测试] 寄存器读取")

        registers = [
            ("有功功率+", "1.0.1.8.0.255"),
            ("有功功率-", "1.0.2.8.0.255"),
            ("电压A相", "1.0.31.7.0.255"),
            ("电流A相", "1.0.51.5.0.255"),
        ]

        with self.create_client().session() as c:
            for name, obis in registers:
                try:
                    attr = cosem.CosemAttribute(
                        interface=enumerations.CosemInterface.REGISTER,
                        instance=Obis.from_string(obis),
                        attribute=2,
                    )
                    data = c.get(attr)

                    # 解析值
                    decoder = a_xdr.AXdrDecoder(
                        encoding_conf=a_xdr.EncodingConf([
                            a_xdr.DoubleLongUnsigned(attribute_name="value")
                        ])
                    )
                    result = decoder.decode(data)
                    value = result.get("value", 0)

                    # 转换单位
                    if "功率" in name:
                        value = value / 100  # 转 kW
                    elif "电压" in name:
                        value = value / 10  # 转 V
                    elif "电流" in name:
                        value = value / 1000  # 转 A

                    print(f"  ✓ {name}: {value:.2f}")
                except Exception as e:
                    print(f"  ✗ {name}: {e}")

    def test_clock(self):
        """测试时钟读取"""
        print("\n[测试] 时钟读取")

        with self.create_client().session() as c:
            try:
                attr = cosem.CosemAttribute(
                    interface=enumerations.CosemInterface.CLOCK,
                    instance=Obis.from_string("0.0.1.0.0.255"),
                    attribute=2,
                )
                data = c.get(attr)

                # 解析时钟
                if len(data) >= 12 and data[0] == 0x09:  # Octet String
                    from dlms_cosem.time import datetime_from_bytes
                    dt = datetime_from_bytes(data)
                    print(f"  ✓ 电表时钟: {dt}")
                    return True
            except Exception as e:
                print(f"  ✗ 时钟读取失败: {e}")
                return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print(f"电表功能测试: {self.host}:{self.port}")
        print("=" * 60)

        tests = [
            ("连接测试", self.test_connection),
            ("时钟测试", self.test_clock),
            ("寄存器测试", self.test_read_registers),
        ]

        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                results.append((name, False))
            time.sleep(1)  # 测试间隔

        # 汇总
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)

        for name, passed in results:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")

        passed = sum(1 for _, p in results if p)
        total = len(results)
        print(f"\n总计: {passed}/{total} 通过")

        return passed == total

if __name__ == "__main__":
    tester = MeterTester("10.32.24.151")
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
```

---

## 常见问题

### Q1: 连接超时怎么办？

```python
# 增加超时时间
tcp_io = BlockingTcpIO(
    host="10.32.24.151",
    port=4059,
    timeout=30,  # 增加到 30 秒
)
```

### Q2: 如何处理不同类型的电表？

```python
# 创建电表配置
METER_CONFIGS = {
    "brand_a": {
        "host": "10.32.24.151",
        "port": 4059,
        "password": "00000000",
        "obis_format": "5byte",
    },
    "brand_b": {
        "host": "10.32.24.152",
        "port": 4059,
        "password": "12345678",
        "obis_format": "6byte",
    },
}

def connect_to_meter(config_name):
    cfg = METER_CONFIGS[config_name]
    # 使用 cfg 创建客户端...
```

### Q3: 如何调试 DLMS 数据？

```python
import logging

# 开启详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 使用 structlog 获得更好的日志
import structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
```

### Q4: 如何测试多个电表？

```python
import concurrent.futures

def test_meter(meter_config):
    """测试单个电表"""
    # 创建客户端并测试
    # ...

def test_multiple_meters(meter_configs):
    """并发测试多个电表"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(test_meter, cfg) for cfg in meter_configs]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return results
```
