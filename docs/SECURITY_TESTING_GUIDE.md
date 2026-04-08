# DLMS/COSEM 安全测试文档

## 测试套件概览

### 1. WPDU (TCP/IP 传输层) 安全测试

**文件**: `tests/test_wpdu_security.py`

**测试覆盖**: 44 个测试用例

| 测试类别 | 测试数量 | 说明 |
|---------|---------|------|
| 连接安全 | 5 | 超时、拒绝、无效主机、边界值 |
| 数据安全 | 4 | 完整性校验、分段、空数据、格式错误 |
| 并发安全 | 2 | 多连接对象、并发发送接收 |
| 异常恢复 | 2 | 优雅关闭、连接后断开 |
| 性能测试 | 2 | 响应时间、缓冲区限制 |
| 安全边界 | 3 | IP验证、端口验证 |
| 配置测试 | 3 | 默认配置、自定义超时、IPv6 |
| HDLC集成 | 2 | HDLC over TCP、帧大小限制 |
| IP Transport | 2 | IPTransport创建、数据包装 |
| 参数化测试 | 7 | 各种配置组合 |
| 边界测试 | 3 | 超时、保留端口 |
| 数据传输 | 3 | 循环传输、大数据、recv_until |
| 错误处理 | 4 | 未连接操作、重复连接 |
| 压力测试 | 2 | 快速连接断开、多次小传输 |

**运行方式**:
```bash
pytest tests/test_wpdu_security.py -v
```

### 2. HDLC (数据链路层) 安全测试

**文件**: `tests/test_hdlc_security.py`

**测试覆盖**: 15 个测试类

| 测试类别 | 说明 |
|---------|------|
| 帧格式安全 | 标志序列、帧验证、FCS计算 |
| 序列号管理 | 序列号范围、溢出处理 |
| 窗口控制 | 窗口大小限制、流量控制帧 |
| 分段重组 | 分段帧、最后分段、最大长度 |
| 地址解析 | 服务器/客户端地址、扩展地址 |
| 连接状态 | 初始状态、状态转换 |
| 控制帧 | SNRM、UA、DISC、DM帧 |
| HDLC传输 | 传输层创建、地址配置 |
| 帧解析 | I帧解析、S帧格式 |
| 参数协商 | SNRM参数、参数范围 |
| 错误恢复 | 超时恢复、重试机制 |
| 边界测试 | 空负载、最大负载 |
| LLC测试 | 命令头、响应头 |
| 性能测试 | 帧创建速度、FCS计算速度 |

**运行方式**:
```bash
pytest tests/test_hdlc_security.py -v
```

### 3. 并发连接能力测试

**文件**: `scripts/test_concurrent_connections.py`

**测试模式**:
- 顺序连接: 作为基准测试
- 并发连接: 多线程同时连接
- 分批连接: 分批次处理
- 连接池: 复用连接

**测试结果** (电表 10.32.24.151:4059):

```
顺序连接测试 (10个):
  成功率: 100%
  总耗时: 7.25秒
  平均连接时间: 725ms
  连接速率: 1.4 连接/秒

并发连接测试 (20个, 5线程):
  成功率: 100%
  总耗时: 3.05秒
  平均连接时间: 604ms
  连接速率: 6.6 连接/秒
```

**运行方式**:
```bash
# 顺序连接
python scripts/test_concurrent_connections.py --mode sequential --max 50

# 并发连接
python scripts/test_concurrent_connections.py --mode threaded --max 100 --workers 10

# 分批连接
python scripts/test_concurrent_connections.py --mode batch --max 200 --batch-size 20

# 连接池测试
python scripts/test_concurrent_connections.py --mode pool --pool-size 10 --operations 100
```

## 并发连接能力分析

### WPDU (TCP/IP) 并发能力

| 环境 | 默认限制 | 可调整 |
|------|---------|--------|
| Windows | 500-1000 | 注册表调整 |
| Linux | 1000-4000 | ulimit -n |

### Serial (串口) 并发能力

| 类型 | 数量 | 说明 |
|------|------|------|
| 标准 PC | 1-4 | 主板自带串口 |
| USB扩展 | 8-32 | USB转串口适配器 |
| 串口服务器 | 16-256 | 网络串口服务器 |

### 推荐配置

```
TCP (WPDU):
  - 使用连接池: 每次 10-50 个连接
  - 使用异步 I/O: asyncio/aiohttp
  - 分批处理: 每批 20-100 个电表

Serial (HDLC):
  - 轮询方式: 每次 1-4 个串口
  - 连接复用: 需要时才连接
  - 串口池: 管理有限资源
```

## 性能优化建议

1. **使用连接池**: 复用 TCP 连接，减少握手开销
2. **批量处理**: 一次读取多个电表数据
3. **异步 I/O**: 使用 asyncio 处理并发
4. **分布式架构**: 多进程/多机器并行处理
5. **缓存机制**: 缓存不常变化的数据

## 测试脚本列表

| 脚本 | 用途 |
|------|------|
| `scripts/test_wpdu_security.py` | WPDU 独立测试脚本 |
| `scripts/test_concurrent_connections.py` | 并发连接能力测试 |
| `scripts/meter_functional_test.py` | 电表功能完整测试 |
| `tests/test_wpdu_security.py` | WPDU pytest 测试套件 |
| `tests/test_hdlc_security.py` | HDLC pytest 测试套件 |
