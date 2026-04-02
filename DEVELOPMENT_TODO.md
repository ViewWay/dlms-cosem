# DLMS/COSEM Library - Development Plan TODO

> 版本: 2026.1.0
> Python 支持: 3.9+
> 构建工具: uv
> 最后更新: 2025-04-01

---

## 最近完成的任务 (2025-04-01)

### ✅ General Block Transfer (P0)
- 实现了 `GeneralBlockTransferRequest` 和 `GeneralBlockTransferResponse` APDU
- 实现了 `BlockTransferStatus` 状态管理
- 在 `DlmsConnection.send()` 中集成了块传输逻辑
- 添加了完整的单元测试 (24 个测试)
- **文件**: `dlms_cosem/protocol/xdlms/general_block_transfer.py`

### ✅ SET With Block & SET With List (P1)
- 实现了 `SetRequestWithFirstBlock` 和 `SetRequestWithBlock`
- 实现了 `SetRequestWithList` 和 `SetRequestWithListFirstBlock`
- 实现了对应的响应类 `SetResponseWithBlock`、`SetResponseLastBlock` 等
- 添加了完整的单元测试

### ✅ ACTION With Block & ACTION With List (P1)
- 实现了 `ActionRequestWithFirstPblock` 和 `ActionRequestNextPblock`
- 实现了 `ActionRequestWithList` 和 `ActionRequestWithListAndFirstPblock`
- 实现了对应的响应类 `ActionResponseWithPblock`、`ActionResponseLastPblock` 等
- 添加了完整的单元测试 (39 个测试)

### ✅ EntryDescriptor (Selective Access P2)
- 实现了 `EntryDescriptor.to_bytes()` 和 `from_bytes()` 方法
- 支持按条目范围和列范围过滤 Profile Generic 数据
- 添加了完整的单元测试 (6 个测试)
- **文件**: `dlms_cosem/cosem/selective_access.py`

---

## 优先级说明

- 🔴 **P0 - Critical**: 生产环境必需，严重影响功能
- 🟡 **P1 - High**: 重要功能缺失，影响标准合规性
- 🟢 **P2 - Medium**: 增强功能，改善用户体验
- ⚪ **P3 - Low**: 可选功能，长期优化

---

## 一、XDLMS 服务补全 (Green Book)

### 1.1 SET 服务扩展 ✅ 完成

#### SET With Block
**状态**: ✅ 已完成
**文件**: `dlms_cosem/protocol/xdlms/set.py:102-142`

```python
@attr.s(auto_attribs=True)
class SetRequestWithFirstBlock:
    """Set-Request-With-First-Datablock ::= SEQUENCE"""
    ...

@attr.s(auto_attribs=True)
class SetRequestWithBlock:
    """Set-Request-With-Datablock ::= SEQUENCE"""
    ...
```

**任务清单**:
- [x] 实现 `SetRequestWithFirstBlock.to_bytes()` / `from_bytes()`
- [x] 实现 `SetRequestWithBlock.to_bytes()` / `from_bytes()`
- [x] 实现 `SetResponseWithBlock` (包含 block_number)
- [x] 实现 `SetResponseLastBlock` (包含 result + block_number)
- [ ] 在 `DlmsClient.set()` 中添加块传输逻辑 (可选)
- [x] 添加单元测试

---

#### SET With List
**状态**: ✅ 已完成
**文件**: `dlms_cosem/protocol/xdlms/set.py:145-190`

**任务清单**:
- [x] 实现 `SetRequestWithList.to_bytes()` / `from_bytes()`
- [x] 实现 `SetRequestWithListFirstBlock`
- [x] 实现 `SetResponseWithList`
- [x] 实现 `SetResponseLastBlockWithList`
- [ ] 在 `DlmsClient` 中添加 `set_many()` 方法 (可选)
- [x] 添加单元测试

---

### 1.2 ACTION 服务扩展 ✅ 完成

#### ACTION With Block
**状态**: ✅ 已完成
**文件**: `dlms_cosem/protocol/xdlms/action.py`

**任务清单**:
- [x] 创建 `ActionRequestWithFirstPblock` 类
- [x] 创建 `ActionRequestNextPblock` 类
- [x] 创建 `ActionResponseWithPblock` 类
- [x] 创建 `ActionResponseLastPblock` 类
- [x] 实现块传输 Action 的工厂模式
- [ ] 在 `DlmsClient.action()` 中添加块传输支持 (可选)
- [x] 添加单元测试

---

#### ACTION With List
**状态**: ✅ 已完成
**文件**: `dlms_cosem/protocol/xdlms/action.py`

**任务清单**:
- [x] 创建 `ActionRequestWithList` 类
- [x] 创建 `ActionResponseWithList` 类
- [x] 实现列表 Action 的响应解析
- [ ] 在 `DlmsClient` 中添加 `action_many()` 方法 (可选)
- [x] 添加单元测试

---

### 1.3 General Block Transfer ✅ 完成

**状态**: ✅ 已完成
**文件**: `dlms_cosem/protocol/xdlms/general_block_transfer.py`

```python
@property
def use_blocks(self) -> bool:
    """If the event should be sent via GlobalBlockTransfer"""
    return self.use_block_transfer and self.conformance.general_block_transfer
```

**任务清单**:
- [x] 实现 `general_block_transfer` APDU 编解码
- [x] 实现 `GeneralBlockTransferRequest` / `GeneralBlockTransferResponse`
- [x] 实现块传输状态管理 (`BlockTransferStatus`)
- [x] 在 `DlmsConnection.send()` 中集成块传输逻辑
- [x] 处理块传输超时和重传
- [x] 添加单元测试 `tests/test_general_block_transfer.py` (24 个测试)
- [x] 更新 conformance `general_block_transfer` 检查

---

### 1.4 Selective Access 完善 ✅ 完成

**状态**: ✅ RangeDescriptor 和 EntryDescriptor 都已完整
**文件**: `dlms_cosem/cosem/selective_access.py`

**任务清单**:
- [x] 实现 `EntryDescriptor.from_bytes()`
- [x] 实现 `EntryDescriptor.to_bytes()`
- [ ] 实现 `selected_values` 在 `RangeDescriptor` 中的完整支持 (可选)
- [x] 在 `GET` 中支持 EntryDescriptor (通过 AccessDescriptorFactory)
- [x] 添加单元测试 (6 个测试)

---

### 1.5 ExceptionResponse 增强 🟢 P2

**状态**: 基础实现，可扩展
**文件**: `dlms_cosem/protocol/xdlms/exception_response.py`

**任务清单**:
- [ ] 支持所有 Service Error 类型的详细解析
- [ ] 添加更友好的错误消息
- [ ] 创建异常层次结构便于捕获
- [ ] 添加错误恢复建议

**依赖**: 无
**预计工作量**: 1-2 天

---

## 二、传输层增强 (Green Book + White Book)

### 2.1 HDLC 参数协商 🟡 P1

**状态**: SNRM 帧信息字段为空
**文件**: `dlms_cosem/hdlc/frames.py:175-183`

```python
@property
def information(self) -> bytes:
    """
    The information field on an SNRM request can be used to negotiate HDLC
    connection parameters, (window size, max_frame_length etc.) It is not supported.
    """
    return b""  # TODO: Implement parameter negotiation
```

**任务清单**:
- [ ] 定义 HDLC 参数结构
- [ ] 实现参数编码/解码
- [ ] 实现 SNRM 参数请求
- [ ] 实现 UA 参数响应
- [ ] 在连接建立时保存协商参数
- [ ] 根据协商参数调整窗口大小
- [ ] 添加单元测试

**依赖**: 无
**预计工作量**: 3-4 天

---

### 2.2 HDLC 窗口机制 🟢 P2

**状态**: 代码注释提到窗口大小未完全支持
**文件**: `dlms_cosem/io.py` (多处注释)

**任务清单**:
- [ ] 实现发送窗口控制
- [ ] 实现接收窗口处理
- [ ] 支持多帧未确认传输
- [ ] 添加窗口超时处理
- [ ] 性能测试和优化

**依赖**: HDLC 参数协商
**预计工作量**: 4-5 天

---

### 2.3 UDP 传输支持 🟢 P2

**状态**: 当前仅支持 TCP
**文件**: `dlms_cosem/io.py`

**任务清单**:
- [ ] 创建 `BlockingUdpIO` 类
- [ ] 实现无连接发送/接收
- [ ] 处理 UDP 数据包边界
- [ ] 添加超时重传机制
- [ ] 创建单元测试
- [ ] 添加使用示例

**依赖**: 无
**预计工作量**: 2-3 天

---

### 2.4 TLS 支持 🔴 P0

**状态**: 未实现
**需求**: 部分智能电表通过 TLS (WSK) 通信

**任务清单**:
- [ ] 设计 TLS 传输接口
- [ ] 实现 `TlsTransport` 类
- [ ] 支持证书验证
- [ ] 支持 WSK (Wrapper over TLS)
- [ ] 添加配置示例
- [ ] 安全性测试

**依赖**: 无
**预计工作量**: 5-7 天

---

## 三、安全功能增强 (Yellow Book)

### 3.1 Security Suite 验证 ✅ 完成

**状态**: 已完成
**文件**: `dlms_cosem/security.py:40-145`, `tests/test_security.py:187-268`

**任务清单**:
- [x] 在所有加密操作前验证密钥长度
- [x] 添加 Security Suite 版本检查
- [x] 拒绝不支持的 Suite 配置
- [x] 更好的错误提示
- [x] 添加配置验证工具

**实现内容**:
- `SecuritySuite` 数据类 - 定义套件 0/1/2 的规范
- `SecuritySuiteNumber` 枚举 - 套件编号
- 验证函数: `validate_security_suite()`, `validate_key_length()`, `validate_system_title()`, `validate_invocation_counter()`, `validate_challenge()`
- `SecurityConfigValidator` - 配置验证器类
- 新增异常: `SecuritySuiteError`, `InvalidSecuritySuiteError`, `KeyLengthError`, `InvalidSecurityConfigurationError`

**依赖**: 无
**完成日期**: 2025-04-01

---

### 3.2 密钥管理工具 🟡 P1

**状态**: 密钥管理依赖用户手动处理

**任务清单**:
- [ ] 创建密钥生成工具 `scripts/generate_keys.py`
- [ ] 支持从配置文件加载密钥
- [ ] 支持环境变量密钥
- [ ] 添加密钥轮换辅助
- [ ] 密钥格式转换工具

**依赖**: 无
**预计工作量**: 2-3 天

---

### 3.3 HLS-ISM 支持 ✅ 完成

**状态**: 已完成
**文件**: `dlms_cosem/security.py`, `tests/test_hls_ism.py`

**任务清单**:
- [x] 研究 HLS-ISM (SHA-256) 规范
- [x] 实现 `HighLevelSecurityISMAuthentication`
- [x] 实现 SM4-GCM/SM4-GMAC (中国国密)
- [x] 实现密钥推导 (KDF)
- [x] 支持 Security Suite 0~5
- [x] 添加单元测试 (13 个测试)
- [ ] 更新文档

**完成日期**: 2026-04-03
---

## 四、COSEM 对象模型 (Blue Book)

### 4.1 COSEM 接口类库 ✅ 完成

**状态**: 已完成 30+ 个 COSEM 接口类
**文件**: `dlms_cosem/cosem/`, `tests/test_cosem_interface_classes.py`

**已实现的接口类**:
- [x] IC001 Data, IC003 Register, IC005 Demand Register
- [x] IC006 Register Activation, IC008 Clock, IC009 Script Table
- [x] IC010 Schedule, IC011 Special Day Table
- [x] IC021 Register Monitor, IC022 Single Action Schedule
- [x] IC061 Register Table, IC012 Association SN
- [x] IC064 Security Setup, IC106 NB-IoT Setup, IC107 LoRaWAN Setup
- [x] 通信类: LP/RS485/Infrared/Modem/AutoAnswer/ModemConfiguration
- [x] 电能/功率/电压/电流/功率因数/频率寄存器
- [x] 事件日志, 费率表 (Season/Week/Day Profile)
- [x] NB-IoT 传输层 (`dlms_cosem/transport/nbiot.py`)
- [x] LoRaWAN 传输层 (`dlms_cosem/transport/lorawan.py`)
- [x] 添加单元测试 (52 个测试)

**完成日期**: 2026-04-03
---

### 4.2 Profile Generic 解析增强 🟡 P1

**状态**: 基础解析存在
**文件**: `dlms_cosem/cosem/profile_generic.py`

**任务清单**:
- [ ] 完整支持 `ReadByRange` 功能
- [ ] 支持 `ReadByEntry` 功能
- [ ] 实现缓冲区解析器
- [ ] 支持列过滤
- [ ] 添加排序和分页
- [ ] 创建使用示例
- [ ] 性能优化（大数据量）

**依赖**: 无
**预计工作量**: 4-5 天

---

### 4.3 Capture Objects 完善 🟢 P2

**状态**: 基础实现
**文件**: `dlms_cosem/cosem/capture_object.py`

**任务清单**:
- [ ] 支持更多捕获对象类型
- [ ] 添加 `data_index` 边界检查
- [ ] 优化捕获对象解析
- [ ] 添加单元测试覆盖

**依赖**: 无
**预计工作量**: 1-2 天

---

## 五、开发工具与测试

### 5.1 测试覆盖率提升 🟡 P1

**当前状态**: 部分模块测试不足

**任务清单**:
- [ ] 设置覆盖率目标: 90%+
- [ ] 添加缺失的单元测试:
  - [ ] `test_hdlc/` - HDLC 帧类型覆盖
  - [ ] `test_acse/` - ACSE APDU 覆盖
  - [ ] `test_xdlms/` - XDLMS APDU 覆盖
  - [ ] `test_security/` - 加密/认证覆盖
  - [ ] `test_transport/` - 传输层覆盖
- [ ] 添加集成测试
- [ ] 添加端到端测试（模拟电表）
- [ ] 设置 CI 覆盖率报告

**依赖**: 无
**预计工作量**: 8-10 天

---

### 5.2 性能基准测试 🟢 P2

**状态**: 无性能测试

**任务清单**:
- [ ] 创建 `benchmarks/` 目录
- [ ] 使用 pytest-bench 或 asv
- [ ] 测试 APDU 编解码性能
- [ ] 测试加密/解密性能
- [ ] 测试大数据传输性能
- [ ] 建立性能基线
- [ ] CI 中运行基准测试

**依赖**: 无
**预计工作量**: 3-4 天

---

### 5.3 Fuzzing 测试 🟢 P2

**状态**: 未进行模糊测试

**任务清单**:
- [ ] 集成 AFL++ 或 libFuzzer
- [ ] 对 APDU 解析进行 fuzzer
- [ ] 对 HDLC 帧解析进行 fuzzer
- [ ] 对 BER/AXDR 解析进行 fuzzer
- [ ] 定期运行 fuzzer 并修复问题

**依赖**: 无
**预计工作量**: 5-7 天

---

## 六、文档与示例

### 6.1 API 文档完善 🟡 P1

**状态**: 部分文档缺失

**任务清单**:
- [ ] 为所有公共 API 添加 docstring
- [ ] 使用 Sphinx 或 MkDocs 生成 API 文档
- [ ] 添加架构图（使用 Mermaid）
- [ ] 添加状态机图
- [ ] 添加序列图
- [ ] 部署文档到 GitHub Pages 或 www.dlms.dev

**依赖**: 无
**预计工作量**: 5-7 天

---

### 6.2 示例代码扩展 🟡 P1

**状态**: 基础示例存在
**目录**: `examples/`

**任务清单**:
- [ ] `examples/associations_list.py` - 增强
- [ ] `examples/dlms_with_hdlc_example.py` - 增强
- [ ] `examples/dlms_with_tcp_example.py` - 增强
- [ ] 添加 `examples/get_with_block.py` - 块读取
- [ ] 添加 `examples/get_with_list.py` - 批量读取
- [ ] 添加 `examples/set_example.py` - 设置示例
- [ ] 添加 `examples/action_example.py` - 方法调用
- [ ] 添加 `examples/data_notification.py` - 数据接收
- [ ] 添加 `examples/profile_generic_reader.py` - 负荷曲线
- [ ] 添加 `examples/hls_authentication.py` - HLS 认证
- [ ] 添加 `examples/tls_connection.py` - TLS 连接
- [ ] 添加 `examples/async_client.py` - 异步客户端

**依赖**: 相关功能实现
**预计工作量**: 4-5 天

---

### 6.3 故障排查指南 🟢 P2

**任务清单**:
- [ ] 创建 `TROUBLESHOOTING.md`
- [ ] 常见错误及解决方案
- [ ] 调试技巧
- [ ] 日志级别说明
- [ ] Wireshark 解析指南

**依赖**: 无
**预计工作量**: 2-3 天

---

## 七、Python 版本与工具链

### 7.1 Python 3.9+ 兼容性维护 🔴 P0

**当前状态**: 支持 3.9-3.13

**任务清单**:
- [ ] CI 中测试所有 Python 版本 (3.9, 3.10, 3.11, 3.12, 3.13)
- [ ] 每次发布前验证最低版本
- [ ] 更新类型注解以兼容 3.9
- [ ] 处理 typing_extensions 需求
- [ ] 文档中说明版本要求

**依赖**: CI 配置
**预计工作量**: 持续

---

### 7.2 uv 工作流完善 🟡 P1

**当前状态**: 基础配置存在

**任务清单**:
- [ ] 更新 `pyproject.toml` 完整配置
- [ ] 确保 `uv.lock` 正常使用
- [ ] 创建 Makefile 或 Justfile 封装常用命令
- [ ] 更新 `scripts/` 目录:
  - [ ] `scripts/dev.sh` - 开发环境设置
  - [ ] `scripts/test.sh` - 运行测试
  - [ ] `scripts/lint.sh` - 代码检查
  - [ ] `scripts/release.sh` - 发布流程
- [ ] 更新 README 中的 uv 使用说明

**依赖**: 无
**预计工作量**: 1-2 天

---

### 7.3 Pre-commit Hooks 增强 🟢 P2

**状态**: 基础配置存在
**文件**: `.pre-commit-config.yaml`

**任务清单**:
- [ ] 添加 mypy 类型检查
- [ ] 添加 ruff 格式化（替代/补充 black）
- [ ] 添加 bandit 安全检查
- [ ] 添加 codespell 拼写检查
- [ ] 添加 markdownlint 文档检查
- [ ] 添加 todo-links 检查
- [ ] 确保所有钩子通过 uv 运行

**依赖**: 无
**预计工作量**: 1-2 天

---

## 八、异步 I/O 支持

### 8.1 异步客户端实现 🟡 P1

**状态**: 当前仅阻塞 I/O

**任务清单**:
- [ ] 设计异步接口（asyncio）
- [ ] 创建 `AsyncTcpIO` 类
- [ ] 创建 `AsyncSerialIO` 类
- [ ] 创建 `AsyncDlmsClient` 类
- [ ] 实现异步连接管理
- [ ] 实现异步请求/响应
- [ ] 添加异步示例
- [ ] 性能对比测试

**依赖**: 无
**预计工作量**: 7-10 天

---

### 8.2 回调/事件驱动模式 🟢 P2

**任务清单**:
- [ ] 设计 DataNotification 回调接口
- [ ] 实现事件监听器
- [ ] 支持多路复用
- [ ] 添加使用示例

**依赖**: 异步 I/O
**预计工作量**: 3-4 天

---

## 九、错误处理与日志

### 9.1 异常层次优化 🟡 P1

**状态**: 异常分散，结构可优化

**任务清单**:
- [ ] 创建完整的异常层次
- [ ] `DlmsException` 基类
- [ ] `DlmsProtocolError` - 协议错误
- [ ] `DlmsSecurityError` - 安全错误
- [ ] `DlmsConnectionError` - 连接错误
- [ ] `DlmsTimeoutError` - 超时错误
- [ ] 添加错误代码枚举
- [ ] 统一错误消息格式

**依赖**: 无
**预计工作量**: 2-3 天

---

### 9.2 结构化日志增强 🟢 P2

**状态**: 使用 structlog，可增强

**任务清单**:
- [ ] 统一日志格式
- [ ] 添加请求追踪 ID
- [ ] 添加敏感信息过滤
- [ ] 添加性能日志
- [ ] 支持日志输出到文件
- [ ] 添加日志配置示例

**依赖**: 无
**预计工作量**: 2-3 天

---

## 十、发布与维护

### 10.1 版本发布流程 🔴 P0

**状态**: 脚本存在，需验证

**任务清单**:
- [ ] 验证 `scripts/release.sh` 功能
- [ ] 添加 CHANGEELONG 自动生成
- [ ] 添加版本号检查
- [ ] 添加发布检查清单
- [ ] 设置 GitHub Actions 自动发布

**依赖**: CI 配置
**预计工作量**: 2-3 天

---

### 10.2 依赖更新策略 🟢 P2

**任务清单**:
- [ ] 设置 Dependabot 或 Renovate
- [ ] 定期更新依赖
- [ ] 安全更新自动 PR
- [ ] 依赖兼容性测试

**依赖**: 无
**预计工作量**: 1-2 天

---

## 十一、长期规划

### 11.1 服务器模式（电表模拟）🟢 P2

**状态**: README 明确说明不支持

**任务清单**:
- [ ] 可行性研究
- [ ] 设计服务器 API
- [ ] 实现基本服务器
- [ ] 用于测试和演示

**依赖**: 核心功能完整
**预计工作量**: 15-20 天

---

### 11.2 多协议扩展 🟢 P2

**任务清单**:
- [ ] 研究其他 ANSI 标准 (C12.22 等)
- [ ] 抽象传输层接口
- [ ] 插件系统设计

**依赖**: 架构重构
**预计工作量**: 10-15 天

---

### 11.3 性能优化 🟢 P2

**任务清单**:
- [ ] APDU 编解码优化
- [ ] 减少内存拷贝
- [ ] Cython/Rust 扩展关键路径
- [ ] 零拷贝解析

**依赖**: 性能基准
**预计工作量**: 10-15 天

---

## 按里程碑分组

### Milestone 1: 核心功能补全 (4-6 周)
- General Block Transfer
- SET With Block
- ACTION With Block
- HDLC 参数协商
- 测试覆盖率 85%+

### Milestone 2: 批量操作 (2-3 周)
- SET With List
- ACTION With List
- Selective Access 完善
- Profile Generic 增强

### Milestone 3: 安全与传输 (3-4 周)
- TLS 支持
- 密钥管理工具
- UDP 传输
- HLS-ISM 支持

### Milestone 4: 开发体验 (2-3 周)
- 异步 I/O
- 文档完善
- 示例扩展
- 错误处理优化

### Milestone 5: 长期规划 (持续)
- COSEM 接口类库
- 服务器模式
- 性能优化

---

## 快速开始检查清单

如果你想贡献代码，请按以下顺序：

1. ✅ 设置开发环境: `uv sync --extra dev`
2. ✅ 运行测试: `uv run pytest`
3. ✅ 运行 linter: `uvx pre-commit run --all-files`
4. 📋 选择一个 P0/P1 任务开始
5. 📋 创建分支: `git checkout -b feature/xxx`
6. 📋 编写代码和测试
7. 📋 提交 PR（欢迎代码展示，但不会直接合并）

---

## 资源链接

- **DLMS UA**: https://www.dlms.com/
- **Blue Book** (COSEM Interface Objects): DLMS UA 1000-1
- **Green Book** (Architecture and Protocols): DLMS UA 1000-1 Ed. 14
- **Yellow Book** (Security): DLMS UA 1000-5
- **White Book** (HDLC): DLMS UA 1000-3
- **项目文档**: https://www.dlms.dev/

---

> 本 TODO 文档会随着项目进展持续更新。
> 如有疑问或建议，请提交 Issue 或联系 info(at)pwit.se
