# DLMS/COSEM HLS 高级加密完整使用指南

## 目录

1. [概述](#概述)
2. [安全套件详解](#安全套件详解)
3. [HLS-GMAC 完整流程](#hls-gmac-完整流程)
4. [密钥管理](#密钥管理)
5. [实际应用示例](#实际应用示例)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

---

## 概述

HLS (High Level Security) 是DLMS/COSEM协议中的高级安全层，提供：

- **数据加密**: 保护通信内容不被窃听
- **消息认证**: 验证数据完整性和来源
- **双向认证**: 客户端和服务器互相验证身份

### 支持的安全套件

| 安全套件 | 认证方式 | 加密算法 | 密钥长度 | 适用场景 |
|---------|---------|---------|---------|---------|
| HLS-ISM | HLS | AES-128-GCM | 16字节 | 标准加密通信 |
| HLS-GMAC | HLS | AES-128-GMAC | 16字节 | 最高级别安全 |
| SM4-GMAC | HLS | SM4 (国标) | 16字节 | 中国国标电表 |
| SM4-GCM | HLS | SM4-GCM | 16字节 | 中国国标扩展 |

---

## 安全套件详解

### HLS-ISM (Initial Security Mechanism)

使用AES-GCM进行数据加密和认证：

```python
from dlms_cosem.security import SecuritySuite

settings = DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
    authentication="hls",
    security_suite=SecuritySuite.HLS_ISM,
    authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
    encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
)
```

### HLS-GMAC (推荐)

最高安全级别，每个消息都进行GMAC认证：

```python
settings = DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
    authentication="hls",
    security_suite=SecuritySuite.HLS_GMAC,
    authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
    encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
    client_system_title=bytes.fromhex("0000000000000000"),
)
```

### SM4-GMAC (中国国标)

使用SM4算法（GB/T 32907）：

```python
settings = DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
    authentication="hls",
    security_suite=SecuritySuite.SM4_GMAC,
    authentication_key=bytes.fromhex("0123456789ABCDEF0123456789ABCDEF"),
    encryption_key=bytes.fromhex("FEDCBA9876543210FEDCBA9876543210"),
    client_system_title=bytes.fromhex("0000000000000000"),
)
```

---

## HLS-GMAC 完整流程

### 1. 连接建立流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    HLS-GMAC 连接建立流程                          │
└─────────────────────────────────────────────────────────────────┘

客户端                          服务器
  │                               │
  │  1. TCP 连接 (端口 4059)       │
  ├─────────────────────────────>│
  │                               │
  │  2. AARQ (公共连接)            │
  │  - 无加密                      │
  │  - 读取帧计数器                │
  ├─────────────────────────────>│
  │  <─────────────────────────────┤ AARE (成功)
  │                               │
  │  3. 断开公共连接                │
  ├─────────────────────────────>│
  │                               │
  │  4. AARQ (HLS加密连接)         │
  │  - 生成认证值                  │
  │  - 发送加密的 InitiateRequest  │
  ├─────────────────────────────>│
  │  <─────────────────────────────┤ AARE (包含服务器认证值)
  │                               │
  │  5. Security Setup (ACTION)    │
  │  - 方法 1: Key Handshake       │
  │  - 交换 Stoken                 │
  ├─────────────────────────────>│
  │  <─────────────────────────────┤ Action Response
  │                               │
  │  ✓ 安全连接建立完成             │
```

### 2. IV (初始化向量) 生成

IV是AES-GCM加密的关键参数，必须唯一：

```python
def generate_iv(frame_counter: int) -> bytes:
    """
    生成 HLS-GMAC IV

    IV 格式 (12字节):
    - 字节 0-1:  0x0000 (固定)
    - 字节 2-11: 帧计数器 (大端序)
    """
    iv = bytearray(12)
    iv[2:6] = frame_counter.to_bytes(4, 'big')
    return bytes(iv)

# 示例
iv = generate_iv(0x4B35)  # 帧计数器 19253
# 结果: 00 00 00 00 00 01 4B 35 00 00 00 00
```

### 3. AAD (附加认证数据) 生成

```python
def generate_aad(authentication_key: bytes) -> bytes:
    """
    生成 HLS-GMAC AAD

    AAD 格式:
    - 0x30 + Authentication Key
    """
    return bytes([0x30]) + authentication_key

# 示例
akey = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
aad = generate_aad(akey)
# 结果: 30 D0 D1 D2 ... DF
```

---

## 密钥管理

### 密钥类型

| 密钥类型 | 用途 | 长度 | 示例值 |
|---------|------|------|--------|
| Authentication Key (AKEY) | 认证和GMAC | 16字节 | D0D1D2D3... |
| Encryption Key (EKEY) | 数据加密 | 16字节 | 00010203... |
| Master Key | 派生其他密钥 | 16字节 | 由电表厂商设置 |

### 密钥派生示例

```python
from hashlib import sha256

def derive_keys(master_key: bytes, server_title: bytes) -> tuple[bytes, bytes]:
    """
    从主密钥派生认证密钥和加密密钥

    Args:
        master_key: 16字节主密钥
        server_title: 8字节服务器系统标题

    Returns:
        (authentication_key, encryption_key)
    """
    # 派生 AKEY: SHA256(Master Key + 0x01 + Server Title)[0:16]
    akey_input = master_key + bytes([0x01]) + server_title
    akey = sha256(akey_input).digest()[:16]

    # 派生 EKEY: SHA256(Master Key + 0x02 + Server Title)[0:16]
    ekey_input = master_key + bytes([0x02]) + server_title
    ekey = sha256(ekey_input).digest()[:16]

    return akey, ekey
```

### 密钥轮换

```python
from dlms_cosem.key_management import KeyManager, KeyRotationSchedule

km = KeyManager()

# 设置密钥
km.set_key("authentication", bytes.fromhex("D0D1...DEF"))
km.set_key("encryption", bytes.fromhex("0001...0E0F"))

# 配置自动轮换
km.schedule_rotation(
    key_type="authentication",
    schedule=KeyRotationSchedule.MONTHLY,
    notify_before_days=7
)
```

---

## 实际应用示例

### 示例1: 完整的HLS连接和数据读取

```python
import asyncio
import logging
from dlms_cosem import AsyncDlmsClient, DlmsConnectionSettings
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport
from dlms_cosem.security import SecuritySuite

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('dlms')


async def read_meter_with_hls():
    """使用HLS-GMAC读取电表数据"""

    # 连接参数
    host = "10.32.24.151"
    port = 4059

    # HLS安全配置
    settings = DlmsConnectionSettings(
        client_logical_address=16,
        server_logical_address=1,
        authentication="hls",
        security_suite=SecuritySuite.HLS_GMAC,
        authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
        encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
        client_system_title=bytes.fromhex("0000000000000000"),
    )

    # 创建连接
    io = TcpIO(host=host, port=port, timeout=10)
    transport = HdlcTransport(io)
    client = AsyncDlmsClient(transport, settings)

    try:
        # 建立连接
        logger.info("正在建立HLS连接...")
        await client.connect()
        logger.info("HLS连接建立成功")

        # 读取设备信息
        meter_id = await client.get("0.0.96.1.0.255")
        logger.info(f"电表ID: {meter_id}")

        # 读取时钟
        clock = await client.get("0.0.1.0.0.255")
        logger.info(f"时钟: {clock}")

        # 读取有功功率
        power = await client.get("1.0.1.8.0.255")
        logger.info(f"有功功率: {power} W")

        # 读取电压
        voltage = await client.get("1.0.31.7.0.255")
        logger.info(f"电压: {voltage} V")

        return {
            "meter_id": meter_id,
            "clock": clock,
            "power": power,
            "voltage": voltage,
        }

    except Exception as e:
        logger.error(f"操作失败: {e}")
        raise
    finally:
        await client.close()
        logger.info("连接已关闭")


# 运行示例
if __name__ == "__main__":
    result = asyncio.run(read_meter_with_hls())
    print(f"\n读取结果: {result}")
```

### 示例2: 批量读取多个电表

```python
import asyncio
from typing import List, Dict


async def read_multiple_meters(meter_configs: List[Dict]) -> List[Dict]:
    """
    并发读取多个电表数据

    Args:
        meter_configs: 电表配置列表
            [{
                "host": "10.32.24.151",
                "port": 4059,
                "akey": "D0D1D2...",
                "ekey": "000102..."
            }, ...]
    """
    async def read_single_meter(config):
        settings = DlmsConnectionSettings(
            client_logical_address=16,
            server_logical_address=1,
            authentication="hls",
            authentication_key=bytes.fromhex(config["akey"]),
            encryption_key=bytes.fromhex(config["ekey"]),
        )

        io = TcpIO(host=config["host"], port=config["port"])
        transport = HdlcTransport(io)
        client = AsyncDlmsClient(transport, settings)

        try:
            await client.connect()
            return {
                "host": config["host"],
                "meter_id": await client.get("0.0.96.1.0.255"),
                "power": await client.get("1.0.1.8.0.255"),
                "voltage": await client.get("1.0.31.7.0.255"),
            }
        except Exception as e:
            return {"host": config["host"], "error": str(e)}
        finally:
            await client.close()

    # 并发读取
    tasks = [read_single_meter(cfg) for cfg in meter_configs]
    return await asyncio.gather(*tasks)


# 使用示例
meters = [
    {"host": "10.32.24.151", "port": 4059, "akey": "D0D1...", "ekey": "0001..."},
    {"host": "10.32.24.152", "port": 4059, "akey": "D0D1...", "ekey": "0001..."},
]

results = asyncio.run(read_multiple_meters(meters))
for r in results:
    print(f"{r['host']}: {r}")
```

### 示例3: 读取负荷曲线数据

```python
async def read_load_profile(client: AsyncDlmsClient, count: int = 10):
    """
    读取负荷曲线数据

    Args:
        client: 已连接的客户端
        count: 读取的记录数量
    """
    # 读取负荷曲线 (OBIS: 1.0.99.1.0.255)
    profile = await client.get(
        "1.0.99.1.0.255",
        access="range",
        from_=0,
        to_=count
    )

    print("\n负荷曲线数据:")
    print("-" * 80)
    print(f"{'时间':<20} {'有功功率(kW)':<15} {'无功功率(kvar)':<15}")
    print("-" * 80)

    for entry in profile:
        timestamp = entry.get("timestamp", "N/A")
        active_power = entry.get("active_power", 0) / 1000  # W转kW
        reactive_power = entry.get("reactive_power", 0) / 1000

        print(f"{timestamp:<20} {active_power:<15.2f} {reactive_power:<15.2f}")
```

---

## 故障排除

### 常见错误及解决方案

#### 1. 认证失败

```
错误: Authentication failed
原因: 密钥不正确或安全套件不匹配
解决方案:
1. 验证AKEY和EKEY是否正确
2. 确认电表使用的是HLS-GMAC还是HLS-ISM
3. 检查client_system_title是否正确
```

#### 2. 加密/解密失败

```
错误: Decryption failed
原因: 帧计数器不同步
解决方案:
1. 重新连接电表
2. 确保使用正确的帧计数器值
3. 检查IV生成是否正确
```

#### 3. 连接超时

```
错误: Connection timeout
原因: 网络问题或电表未响应
解决方案:
1. 检查网络连接
2. 确认电表IP地址和端口
3. 增加超时时间
```

### 调试模式

```python
import structlog

# 配置详细日志
structlog.configure(
    logger_name='dlms',
    level='DEBUG',
    handlers=[
        structlog.dev.ConsoleRenderer()
    ]
)

# 启用原始数据日志
import dlms_cosem.debug
dlms_cosem.debug.enable_raw_log()
```

---

## 最佳实践

### 1. 密钥安全

- ✅ 将密钥存储在安全的密钥管理系统中
- ✅ 使用环境变量或配置文件（不要硬编码）
- ✅ 定期轮换密钥
- ❌ 不要在代码中硬编码密钥
- ❌ 不要将密钥提交到版本控制系统

### 2. 连接管理

```python
# 使用上下文管理器确保连接关闭
async with create_hls_client(settings) as client:
    data = await client.get("0.0.96.1.0.255")
# 连接自动关闭
```

### 3. 错误处理

```python
from dlms_cosem.exceptions import (
    DlmsConnectionError,
    DlmsAuthenticationError,
    DlmsTimeoutError
)

try:
    await client.connect()
except DlmsAuthenticationError:
    logger.error("认证失败: 检查密钥配置")
except DlmsTimeoutError:
    logger.error("连接超时: 检查网络连接")
except DlmsConnectionError as e:
    logger.error(f"连接错误: {e}")
```

### 4. 性能优化

```python
# 复用连接
class MeterConnectionPool:
    def __init__(self):
        self.connections = {}

    async def get_connection(self, host: str, port: int):
        key = f"{host}:{port}"
        if key not in self.connections:
            self.connections[key] = await self._create_connection(host, port)
        return self.connections[key]
```

---

## 附录

### A. OBIS代码参考

| 描述 | OBIS代码 | 属性 |
|------|---------|------|
| 电表ID | 0.0.96.1.0.255 | 2 |
| 时钟 | 0.0.1.0.0.255 | 2 |
| 有功功率 | 1.0.1.8.0.255 | 2 |
| 无功功率 | 1.0.3.8.0.255 | 2 |
| 电压 | 1.0.31.7.0.255 | 2 |
| 电流 | 1.0.31.7.0.255 | 3 |
| 功率因数 | 1.0.13.7.0.255 | 2 |
| 负荷曲线 | 1.0.99.1.0.255 | - |

### B. 安全套件代码参考

```python
class SecuritySuite(IntEnum):
    """DLMS安全套件"""
    NONE = 0
    LLS = 1
    HLS_ISM = 2
    HLS_GMAC = 3
    HLS_GMAC_WITH_CIPHER_SUITE = 4
    SM4_GMAC = 5
    SM4_GCM = 6
```

### C. 参考资料

- IEC 62056-53: DLMS/COSEM Application Layer
- IEC 62056-62: COSEM Interface Classes
- GB/T 17215.6: 中国DLMS扩展
- GB/T 32907: SM4加密算法
