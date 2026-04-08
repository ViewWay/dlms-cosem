# DLMS/COSEM 电表连接指南

本文档说明如何使用 dlms-cosem 库连接实际电表。

## 硬件要求

### 串口连接 (RS-485 / 光学头)
- USB 转 RS-485 转换器
- 或 USB 光学读表头 (支持 IEC 62056-21)
- 电表支持串口通信

### TCP/IP 连接
- 网线连接到电表
- 或通过转换器 (RS-485 → TCP)
- 知道电表的 IP 地址和端口

## 安装依赖

```bash
pip install dlms-cosem

# 如果使用串口，确保 pyserial 已安装
pip install pyserial
```

## 连接方式

### 1. 串口 (HDLC)

```python
from dlms_cosem import cosem, enumerations
from dlms_cosem.client import DlmsClient
from dlms_cosem.io import SerialIO, HdlcTransport
from dlms_cosem.security import NoSecurityAuthentication

# 创建串口 IO
serial_io = SerialIO(
    port_name="COM3",        # Windows: COM3, COM4...
    # port_name="/dev/ttyUSB0",  # Linux: /dev/ttyUSB0
    baud_rate=9600,
    timeout=10
)

# 创建 HDLC 传输层
transport = HdlcTransport(
    client_logical_address=16,
    server_logical_address=1,
    server_physical_address=17,
    io=serial_io,
)

# 创建客户端
client = DlmsClient(
    transport=transport,
    authentication=NoSecurityAuthentication(),
)

# 连接并读取数据
with client.session() as c:
    # 读取电表 ID
    meter_id_attr = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=cosem.Obis.from_string("0.0.96.1.0.255"),
        attribute=2,
    )
    data = c.get(meter_id_attr)
    print(f"Meter ID: {data.hex()}")
```

### 2. TCP/IP 连接

```python
from dlms_cosem import cosem, enumerations
from dlms_cosem.client import DlmsClient
from dlms_cosem.io import BlockingTcpIO, TcpTransport
from dlms_cosem.security import NoSecurityAuthentication

# 创建 TCP IO
tcp_io = BlockingTcpIO(
    host="192.168.1.100",
    port=4059,
    timeout=10
)

# 创建 TCP 传输层
transport = TcpTransport(
    client_logical_address=16,
    server_logical_address=1,
    io=tcp_io,
)

# 创建客户端
client = DlmsClient(
    transport=transport,
    authentication=NoSecurityAuthentication(),
)

# 连接并读取数据
with client.session() as c:
    # 读取电表 ID
    meter_id_attr = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.DATA,
        instance=cosem.Obis.from_string("0.0.96.1.0.255"),
        attribute=2,
    )
    data = c.get(meter_id_attr)
    print(f"Meter ID: {data.hex()}")
```

### 3. 带密码认证 (Low-Level)

```python
from dlms_cosem.security import LowLevelAuthentication

client = DlmsClient(
    transport=transport,
    authentication=LowLevelAuthentication(
        password=b"12345678"  # 8 字节密码
    ),
)
```

### 4. HLS-GMAC 认证 (高安全级别)

```python
from dlms_cosem.security import HighLevelSecurityGmacAuthentication

encryption_key = bytes.fromhex("990EB3136F283EDB44A79F15F0BFCC21")
authentication_key = bytes.fromhex("EC29E2F4BD7D697394B190827CE3DD9A")

client = DlmsClient(
    transport=transport,
    authentication=HighLevelSecurityGmacAuthentication(challenge_length=32),
    encryption_key=encryption_key,
    authentication_key=authentication_key,
)
```

## 常用 OBIS 代码

| OBIS 代码 | 描述 |
|-----------|------|
| `0.0.96.1.0.255` | 电表 ID |
| `0.0.1.0.0.255` | 时钟 |
| `1.0.1.8.0.255` | 有功功率 (+) |
| `1.0.31.7.0.255` | A 相电压 |
| `1.0.51.5.0.255` | A 相电流 |
| `1.0.99.1.0.255` | 负荷_profile |

## 故障排查

### 连接失败

1. **串口无法打开**
   - 检查串口是否被其他程序占用
   - Windows: 设备管理器查看 COM 口
   - Linux: `ls /dev/ttyUSB*`

2. **TCP 连接超时**
   - 检查 IP 地址是否正确
   - 检查端口是否正确 (默认 4059)
   - 检查防火墙设置
   - 使用 `ping` 测试连通性

### 读取失败

1. **认证失败**
   - 检查密码是否正确
   - 某些电表需要先无认证连接获取 invocation counter

2. **数据解析错误**
   - 检查 OBIS 代码是否正确
   - 某些电表可能不支持某些对象

## 快速测试

使用提供的快速测试脚本：

```bash
# 串口连接
python scripts/quick_start_meter.py --serial COM3 --verbose

# TCP 连接
python scripts/quick_start_meter.py --tcp 192.168.1.100 --verbose

# 带密码
python scripts/quick_start_meter.py --serial COM3 --password 3132333435363738
```
