# HLS 连接报文完整分析

## 报文来源
- **电表**: KFM1000100000002 (1P2W_SP 单相电能表)
- **地址**: 10.32.24.151:4059
- **测试时间**: 2026-04-08 20:48:12 - 20:49:27

## 加密密钥
```
AKEY (Authentication Key): D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF
EKEY (Encryption Key):    000102030405060708090A0B0C0D0E0F
```

---

## 阶段 1: 公共连接 (无加密)

### 1.1 TCP 连接
```
[20:48:14.165] Connection [10.32.24.151:4059] successful
```

### 1.2 AARQ (Association Request) - 公共连接
```
Hex: 00 01 00 10 00 01 00 2B 60 29 A1 09 06 07 60 85 74 05 08 01 01 
     A6 0A 04 08 00 00 00 00 00 00 00 00 BE 10 04 0E 01 00 00 00 06 5F 1F 
     04 00 00 1F 1F FF FF

Wrapper Header:
  - Version: 0x0001
  - Source WPort: 16 (client)
  - Dest WPort: 1 (meter)
  - Length: 43 (0x2B)

APDU (AARQ):
  - Tag: 0x60 (AARQ)
  - Length: 41 (0x29)
  - Context: LN (Logical Name) - 60 85 74 05 08 01 01
  - Calling AP Title: 0000000000000000
  - Conformance Bits: 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF
    - Bit 0: Get
    - Bit 1: Set
    - Bit 2: Action
    - Bit 4: Event Notification
    - Bit 5: Selective Access
    - Bit 6: Multiple References
    - Bit 10: Block Transfer With Get
    - Bit 11: Block Transfer With Set
    - Bit 12: Block Transfer With Action
  - Proposed Max PDU Size: 0xFFFF (65535)
```

### 1.3 AARE (Association Response) - 公共连接
```
Hex: 00 01 00 01 00 10 00 2B 61 29 A1 09 06 07 60 85 74 05 08 01 01 
     A2 03 02 01 00 A3 05 A1 03 02 01 00 BE 10 04 0E 08 00 06 5F 1F 
     04 00 00 12 10 04 C8 00 07

APDU (AARE):
  - Tag: 0x61 (AARE)
  - Result: 0x00 (Accepted)
  - Diagnostic: 0x00 (No error)
  - Negotiated Conformance: 08 00 (Get, Multiple References, Block Transfer With Get)
  - Negotiated Max PDU Size: 0x04C8 (1228 bytes)
  - VAA Name: 0x0007
```

### 1.4 GET 设备号
```
Request:
  OBIS: 0.0.42.0.0.255 (设备逻辑地址)
  Attribute: 2 (设备号)
  
  Hex: 00 01 00 10 00 01 00 0D C0 01 C1 00 01 00 00 2A 00 00 FF 02 00
       - Tag: 0xC0 (GET_REQUEST_NORMAL)
       - Invoke ID: 0xC1
       - Class ID: 0x0001
       - Instance: 00002A0000FF
       - Attribute ID: 2

Response:
  Hex: 00 01 00 01 00 10 00 16 C4 01 C1 00 09 10 4B 46 4D 31 30 30 30 31 
       30 30 30 30 30 30 30 32
       - Tag: 0xC4 (GET_RESPONSE_NORMAL)
       - Device Number: "KFM1000100000002"
```

### 1.5 GET 帧计数器
```
Request:
  OBIS: 0.0.43.1.0.255 (安全模块帧计数器)
  Attribute: 2

Response:
  Frame Counter: 0x00004B35 (19253)
```

### 1.6 RLRQ (断开公共连接)
```
Hex: 00 01 00 10 00 01 00 17 62 15 80 01 00 BE 10 04 0E 01 00 00 00 06 
     5F 1F 04 00 00 1F 1F FF FF
  - Tag: 0x62 (RLRQ)
  - Reason: 0x80 (Normal)
```

---

## 阶段 2: HLS 加密连接

### 2.1 TCP 重连
```
[20:48:17.444] Connection [10.32.24.151:4059] successful
```

### 2.2 AARQ (HLS-GMAC 加密)
```
Hex: 00 01 00 01 00 01 00 5F 60 5D A1 09 06 07 60 85 74 05 08 01 03 
     A6 0A 04 08 00 00 00 00 00 00 00 00 8A 02 07 80 8B 07 60 85 74 
     05 08 02 05 AC 12 80 10 73 36 55 4C 55 33 37 36 63 5A 45 6F 61 79 
     50 6C BE 23 04 21 21 1F 30 00 00 4B 36 8C 4E A2 6D 0F 47 DE E7 
     D2 01 4E DF D4 00 2A 0F 3F B3 14 0E 01 FE 06 CC DB 90

加密参数:
  - IV: 000000000000000000004B36
  - AAD: 30 D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 DA DB DC DD DE DF (0x30 + AKEY)
  - PlainData: 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF
  - CipherData: 8C 4E A2 6D 0F 47 DE E7 D2 01 4E DF D4 00
  - CipherTag: 2A 0F 3F B3 14 0E 01 FE 06 CC DB 90

认证信息:
  - Context: LNC (Logical Name with Ciphering)
  - Mechanism: HLS-GMAC (0x08 02 05 = 60 85 74 05 08 02 05)
  - Auth Value: "7336554C55333736635A456F6179506C" (从帧计数器生成)
```

### 2.3 AARE (HLS-GMAC 加密响应)
```
加密参数:
  - IV: 4B 46 4D 64 10 00 00 02 00 00 41 3A
  - PlainData: 08 00 06 5F 1F 04 00 00 1E 1D 04 C8 00 07
  - Result: Accepted (0x00)
  - Diagnostic: 0x0E (Authentication required)

服务器信息:
  - Server Title: 4B 46 4D 64 10 00 00 02 (KFMd 10 00 00 02)
  - Stoken: E1 74 F6 AC A2 1F 02 24 5E F7 91 1B 54 AF 84 D5
```

### 2.4 GMAC ACTION (安全设置)
```
Request (加密):
  - IC: 0x000F (Security Setup)
  - Method: 0x01 (Key Handshake)
  - GMAC Tag: CB 2C 07 9B 6B F3 D8 17 E8 A4 40 8B

Response (加密):
  - Return: Stoken (100000413B55175DD868AE07E0E1639C00)
  - GMAC Tag: 55 17 5D D8 68 AE 07 E0 E1 63 9C 00
```

---

## 阶段 3: GET 操作 (加密)

### 3.1 GET 时钟 (0.0.1.0.0.255 attr 2)
```
Request:
  IV: 000000000000000000004B39
  AAD: 30 + AKEY
  PlainData: C0 01 C1 00 08 00 00 01 00 00 FF 02 00
  CipherData: 9E 5F 51 92 0D F4 8D 8E 86 CD 65 86 3B
  CipherTag: C7 7A 89 CA D7 23 1E 5C F3 A3 B4 FE

Response:
  IV: 4B 46 4D 64 10 00 00 02 00 00 41 3D
  PlainData: C4 01 C1 00 09 0C 07 EA 04 04 06 04 04 2B 00 FE 98 01
  Clock Value: 07 EA 04 04 06 04 04 2B 00 FE 98 01
```

---

## 阶段 4: SET 操作 (加密)

### 4.1 SET 时钟 (0.0.1.0.0.255 attr 2)
```
Request:
  IV: 000000000000000000004B3F
  PlainData: C1 01 C1 00 08 00 00 01 00 00 FF 02 00 09 0C 07 EA 
              04 08 03 14 31 1A 00 80 00 FF
  New Clock: 07 EA 04 08 03 14 31 1A 00 80 00 FF
  CipherData: C7 BD F1 8D 00 01 71 20 6E 10 2A 91 29 B0 AE CC 05 DB 7B 95
  CipherTag: 51 BE 6C FB 1D D5 20 57 19 45 48 6A 6D AD 27 1A 95 E3 1C

Response:
  IV: 4B 46 4D 64 10 00 00 02 00 00 41 42
  PlainData: C5 01 C1 00 (Success)
```

---

## 阶段 5: 断开连接 (加密)

### 5.1 RLRQ (加密)
```
IV: 000000000000000000004B3A
PlainData: 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF
```

### 5.2 RLRE (加密响应)
```
IV: 4B 46 4D 64 10 00 00 02 00 00 41 3E
PlainData: 08 00 06 5F 1F 04 00 00 1E 1D 04 C8 00 07
```

---

## 帧计数器演变

| 操作 | 计数器 | 说明 |
|------|--------|------|
| 初始读取 | 0x4B35 | 19253 |
| HLS AARE | 0x413A | 16698 (服务器) |
| GMAC ACTION 请求 | 0x4B38 | - |
| GMAC ACTION 响应 | 0x413C | 16699 (服务器) |
| GET CLOCK 请求 | 0x4B39 | - |
| GET CLOCK 响应 | 0x413D | 16700 (服务器) |
| SET CLOCK 请求 | 0x4B3F | - |
| SET CLOCK 响应 | 0x4142 | 16706 (服务器) |
| RLRQ | 0x4B3A | - |
| RLRE | 0x413E | 16702 (服务器) |

---

## 关键参数说明

1. **Wrapper Header 格式**:
   - 版本 (2字节) + 源WPort (4字节) + 目标WPort (4字节) + 长度 (4字节) + APDU

2. **AES-GCM 加密**:
   - 密钥长度: 128位
   - IV长度: 12字节
   - Tag长度: 12字节
   - AAD: 0x30 + AKEY (用于完整性认证)

3. **帧计数器管理**:
   - 请求计数器: 客户端维护
   - 响应计数器: 服务器维护
   - 计数器值用于生成IV，保证每次加密唯一

4. **GMAC认证**:
   - IC: 0x000F (Security Setup)
   - 方法1: 双向认证，交换Stoken
