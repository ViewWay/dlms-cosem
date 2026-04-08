# HLS (High Level Security) 使用指南

## 概述

HLS (High Level Security) 是DLMS/COSEM协议中的高级安全机制，支持多种加密和认证方式。本指南重点介绍 **HLS-GMAC**，这是最安全的加密方式。

## 认证方式对比

| 方式 | 安全等级 | 加密 | 说明 |
|------|----------|------|------|
| LLS (Low Level Security) | 低 | 无 | 仅密码认证，无加密 |
| HLS-ISM | 中 | AES-GCM-128 | 仅数据加密 |
| HLS-GMAC | 高 | AES-GCM-128 | 数据加密+消息认证 |

## HLS-GMAC 工作流程

```
客户端                                              电表服务器
    │                                                  │
    ├─ 1. TCP连接                                      │
    │                                                  │
    ├─ 2. 公共连接 (AARQ/AARE)                          │
    │   ├─ 读取设备号                                   │
    │   └─ 读取帧计数器                                 │
    │                                                  │
    ├─ 3. 断开公共连接                                  │
    │                                                  │
    ├─ 4. HLS加密连接 (AARQ/AARE)                       │
    │   ├─ 生成IV (帧计数器)                            │
    │   ├─ AAD (0x30 + AKEY)                            │
    │   ├─ 加密InitiateRequest                         │
    │   └─ 发送认证值                                   │
    │                                                  │
    ├─ 5. GMAC双向认证 (ACTION)                        │
    │   ├─ IC 0x000F (Security Setup)                   │
    │   ├─ 交换Stoken                                   │
    │   └─ 验证GMAC标签                                 │
    │                                                  │
    ├─ 6. GET/SET/ACTION 操作 (加密)                     │
    │   ├─ 每次操作使用独立IV                            │
    │   ├─ 请求数据加密                                   │
    │   └─ 响应数据解密                                   │
    │                                                  │
    └─ 7. 断开连接 (RLRQ/RLRE)                         │
```

## 加密参数说明

### 密钥配置
```python
AKEY = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
EKEY = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
```

### IV (初始化向量) 生成

```
IV 格式 (12字节):
  - 字节 0-1:  0x0000 (固定)
  - 字节 2-11: 帧计数器值
```

### AAD (附加认证数据)

```
AAD = 0x30 + AKEY
```

## 完整代码示例

### HLS连接并读取时钟

```python
import asyncio
from dlms_cosem import AsyncDlmsClient, DlmsConnectionSettings
from dlms_cosem.io import TcpIO
from dlms_cosem.transport import HdlcTransport

async def read_meter_with_hls():
    # 配置HLS-GMAC参数
    settings = DlmsConnectionSettings(
        client_logical_address=16,
        server_logical_address=1,
        authentication="hls",
        authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
        encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
        client_system_title=bytes.fromhex("0000000000000000"),
    )

    # 创建TCP连接
    io = TcpIO(host="10.32.24.151", port=4059)
    transport = HdlcTransport(io)
    client = AsyncDlmsClient(transport, settings)

    # 连接并读取时钟
    await client.connect()

    # GET时钟 (0.0.1.0.0.255 attribute 2)
    clock_value = await client.get("0.0.1.0.0.255")
    print(f"Clock: {clock_value}")

    # 断开连接
    await client.close()

# 运行
asyncio.run(read_meter_with_hls())
```

### SET操作 (设置时钟)

```python
async def set_clock_with_hls():
    settings = DlmsConnectionSettings(
        client_logical_address=16,
        server_logical_address=1,
        authentication="hls",
        authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
        encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
    )

    io = TcpIO(host="10.32.24.151", port=4059)
    transport = HdlcTransport(io)
    client = AsyncDlmsClient(transport, settings)

    await client.connect()

    # SET时钟
    new_clock = bytes.fromhex("07EA04080314311A008000FF")
    await client.set("0.0.1.0.0.255", data=new_clock)

    await client.close()
```

### ACTION操作 (GMAC认证)

```python
async def security_setup_action():
    settings = DlmsConnectionSettings(
        client_logical_address=16,
        server_logical_address=1,
        authentication="hls",
        authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
        encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
    )

    io = TcpIO(host="10.32.24.151", port=4059)
    transport = HdlcTransport(io)
    client = AsyncDlmsClient(transport, settings)

    await client.connect()

    # Security Setup action
    # IC: 0x000F (Security Setup)
    # Method: 0x01 (Key Handshake)
    result = await client.action(
        "0.0.0.0.0.255",  # IC 0x000F 的逻辑名
        1,                      # 方法 1
        data=b"\x10\x00\x00\x41\x3B"  # 参数
    )

    print(f"Security Setup result: {result}")

    await client.close()
```

## 帧计数器管理

HLS连接需要维护帧计数器：

```python
# 帧计数器初始值
frame_counter = 0x4B35  # 19253

# 每次加密操作后递增
# 客户端发送: 使用本地计数器
# 服务器响应: 使用服务器计数器
```

## 错误处理

```python
try:
    await client.connect()
except Exception as e:
    if "authentication" in str(e).lower():
        print("认证失败 - 检查密钥配置")
    elif "timeout" in str(e).lower():
        print("连接超时 - 检查网络和电表地址")
    else:
        print(f"连接失败: {e}")
```

## 安全注意事项

1. **密钥管理**
   - AKEY和EKEY应妥善保管
   - 定期更换密钥
   - 不要在代码中硬编码密钥

2. **帧计数器**
   - 每次连接前读取当前帧计数器
   - 保持计数器同步

3. **IV唯一性**
   - 每次加密操作必须使用唯一IV
   - IV由帧计数器生成

4. **认证值生成**
   - 认证值通常由帧计数器经过加密生成
   - 不同厂商可能有不同的认证值生成方式

## 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用structlog
import structlog
structlog.configure(logger_name='dlms', level='DEBUG')
```

### 验证加密参数

```python
# 打印加密参数
print(f"AKEY: {settings.authentication_key.hex().upper()}")
print(f"EKEY: {settings.encryption_key.hex().upper()}")
print(f"Client Title: {settings.client_system_title.hex().upper()}")
```

### 捕获原始报文

```python
# 设置底层日志
import dlms_cosem.debug
dlms_cosem.debug.set_log_level('raw')
```

## 常见问题

### Q: 连接失败，提示"Authentication required"
A: 
- 检查authentication参数是否设置为"hls"
- 验证AKEY和EKEY是否正确
- 确认电表支持HLS-GMAC

### Q: 解密失败
A:
- 检查帧计数器是否同步
- 验证AAD是否正确 (0x30 + AKEY)
- 确认IV是否正确生成

### Q: GMAC认证失败
A:
- 确认Security Setup action是否成功执行
- 验证Stoken是否正确交换
- 检查GMAC标签计算

## 测试脚本

完整的HLS测试脚本位于：
- `tests/test_hls_complete.py` - 完整HLS测试
- `tests/test_hls_flow_analysis.py` - 报文解析测试

测试日志位于：
- `HLS_TEST_LOG.txt` - 测试执行日志
- `docs/HLS/HLS_PACKET_ANALYSIS.md` - 报文详细分析
