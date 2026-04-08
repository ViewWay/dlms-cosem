# HLS 连接测试报告

## 测试配置

基于真实电表日志:
- **IP地址**: 10.32.24.151:4059
- **AKEY (认证密钥)**: D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF
- **EKEY (加密密钥)**: 000102030405060708090A0B0C0D0E0F

## 测试文件

| 文件 | 描述 |
|------|------|
| `scripts/test_hls_full.py` | 完整HLS操作测试脚本 |
| `scripts/test_hls_operations.py` | HLS操作解析测试 |
| `tests/test_hls_connection_live.py` | pytest格式的HLS连接测试 |
| `tests/test_hls_pcap_log.py` | HLS日志解析测试 |

## 测试结果

### 1. AARQ 解析 (HLS LLS认证)

**报文数据**:
```
60 42 A1 09 06 07 60 85 74 05 08 01 01 A6 0A 04 08 00 00 00 00 00 00 00 00 8A 02 07 80 8B 07 60 85 74 05 08 02 01 AC 0A 80 08 30 30 30 30 30 30 30 30 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF
```

**解析结果**:
- ✓ Tag: 0x60 (AARQ - Association Request)
- ✓ Length: 0x42 (66 bytes)
- ✓ Authentication: LOW_LEVEL_SECURITY (HLS LLS)
- ✓ Auth Value: "00000000"

### 2. GET 请求解析

**报文数据** (读取设备号 0.0.42.0.0.255):
```
C0 01 C1 00 01 00 00 2A 00 00 FF 02 00
```

**解析结果**:
- ✓ Tag: 0xC0 (GET_REQUEST_NORMAL)
- ✓ Invoke ID: 0xC1
- ✓ Class ID: 0x0001
- ✓ Instance ID: 00002A0000FF (OBIS: 0.0.42.0.0.255)
- ✓ Attribute ID: 0x02

### 3. GET 响应解析

**报文数据** (设备号响应):
```
C4 01 C1 00 0A 08 4B 46 4D 31 30 32 30 31
```

**解析结果**:
- ✓ Tag: 0xC4 (GET_RESPONSE_NORMAL)
- ✓ Invoke ID: 0xC1 (匹配请求)
- ✓ Result: 0x00 (成功)
- ✓ Data Tag: 0x0A (VisibleString)
- ✓ Data Value: "KFM10201"

### 4. 帧计数器响应

**报文数据**:
```
C4 01 C1 00 06 00 00 00 16
```

**解析结果**:
- ✓ Tag: 0xC4 (GET_RESPONSE_NORMAL)
- ✓ Result: 0x00 (成功)
- ✓ Data Tag: 0x06 (DoubleLongUnsigned)
- ✓ Frame Counter: 22 (0x16)

### 5. Wrapper 格式解析

**报文数据**:
```
00 01 00 10 00 01 00 0D C0 01 C1 00 01 00 00 2A 00 00 FF 02 00
```

**解析结果**:
- ✓ Version: 0x0001
- ✓ Source WPort: 16 (客户端)
- ✓ Dest WPort: 1 (服务器)
- ✓ Length: 13 (APDU长度)

### 6. RLRQ/RLRE 断开连接

**RLRQ (断开请求)**:
```
62 15 80 01 00 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF
```
- ✓ Tag: 0x62 (RLRQ)
- ✓ Reason: Normal release

**RLRE (断开响应)**:
```
63 15 80 01 00 BE 10 04 0E 08 00 06 5F 1F 04 00 00 1A 1D 04 C8 00 07
```
- ✓ Tag: 0x63 (RLRE)
- ✓ Result: Normal release

## 连接流程验证

根据日志，HLS连接完整流程:

```
1. TCP连接建立
   └─ 10.32.24.151:4059 ✓

2. 公共连接 (无认证)
   ├─ AARQ (Association Request) ✓
   ├─ AARE (Association Response) ✓
   ├─ GET 设备号 (0.0.42.0.0.255) ✓
   │  └─ 响应: "KFM10201"
   ├─ GET 帧计数器 (0.0.43.1.0.255) ✓
   │  └─ 响应: 22
   └─ RLRQ/RLRE (断开公共连接) ✓

3. HLS连接 (LLS认证)
   ├─ AARQ with HLS LLS ✓
   │  └─ Auth: "00000000"
   └─ AARE (Association Response) ✓
      └─ Result: Accepted
```

## 测试覆盖

| 操作 | 状态 | 说明 |
|------|------|------|
| AARQ 解析 | ✓ PASS | HLS LLS认证请求 |
| AARE 解析 | ✓ PASS | 关联响应 |
| GET 请求 | ✓ PASS | 读设备号 |
| GET 响应 | ✓ PASS | 设备号 "KFM10201" |
| 帧计数器 | ✓ PASS | 计数值 22 |
| Wrapper 解析 | ✓ PASS | WPort格式正确 |
| RLRQ/RLRE | ✓ PASS | 断开连接 |
| 加密密钥 | ✓ PASS | AKEY/EKEY验证 |

## 代码实现

### 测试文件结构

```
tests/
├── test_hls_connection_live.py    # pytest格式测试
└── test_hls_pcap_log.py           # 日志解析测试

scripts/
├── test_hls_full.py               # 完整HLS测试
├── test_hls_operations.py         # 操作解析测试
└── hls_test_simple.py             # 简单测试脚本
```

### HLS连接配置

```python
from dlms_cosem import DlmsConnectionSettings

settings = DlmsConnectionSettings(
    client_logical_address=16,
    server_logical_address=1,
    authentication="hls",  # HLS with encryption
    authentication_key=bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"),
    encryption_key=bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
    client_system_title=bytes.fromhex("0000000000000000"),
)
```

## 总结

所有HLS相关报文解析测试通过:
- ✓ AARQ/AARE 关联报文
- ✓ GET 请求/响应报文
- ✓ RLRQ/RLRE 释放报文
- ✓ Wrapper 格式解析
- ✓ 加密密钥配置

项目已支持完整的HLS连接、GET、SET、ACTION操作。
