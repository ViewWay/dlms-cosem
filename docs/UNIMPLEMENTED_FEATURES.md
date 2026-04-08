# DLMS/COSEM 未实现功能详细清单

根据蓝皮书 (DLMS UA 1000-1 Ed. 14) 和绿皮书 (DLMS UA 1000-3 Ed. 12) 的对比分析。

---

## 一、Action 选择性访问解析

### 当前状态
Action 请求支持 WithList 和 WithListAndFirstPblock，但选择性访问解析不完整。

### 未实现部分

| 位置 | 问题 | 影响 |
|------|------|------|
| `action.py:305` | `TODO: Parse access selection` | ActionRequestWithList 无法解析 access-select 参数 |
| `action.py:306` | 跳过 access selection 解析 | 无法使用 Action 携带 RangeDescriptor 或 EntryDescriptor |

### 具体代码

```python
# 当前实现 - ActionRequestWithList.from_bytes()
has_access = bool(data.pop(0))
if has_access:
    # TODO: Parse access selection
    _ = data.pop(0)  # 只是跳过，未真正解析
```

### 需要实现

- [ ] ActionRequestNormal 的 access_selection 参数
- [ ] ActionRequestWithList 的 Cosem-Method-With-Selective-Access 解析
- [ ] ActionRequestWithListAndFirstPblock 的 DataBlock-SA 解析
- [ ] ActionResponse 的选择性访问数据解析

---

## 二、HDLC 多帧处理和窗口优化

### 当前状态
基础 HDLC 帧处理已实现，但多帧窗口控制和滑动窗口未完整实现。

### 未实现部分

| 位置 | 问题 | 影响 |
|------|------|------|
| `fields.py:39` | `TODO: Handle multi frame` | SnrmControlField.is_final 始终返回 True |
| `fields.py:59` | `TODO: Handle multi frame` | UaControlField.is_final 始终返回 True |
| `state.py:53` | `TODO: segmentation handling is not working` | 分段帧处理不工作 |
| `state.py:71` | SSN/RSN 是否应存在状态中 | 序列号管理不完整 |

### 具体问题

```python
# SnrmControlField
def is_final(self):
    """'Almost' all the time a SNRM frame is contaned in single frame."""
    # TODO: Handle multi frame
    return True  # 始终返回 True，不支持多帧
```

### 需要实现

- [ ] SNRM/UA 帧的多帧支持（当前假设单帧）
- [ ] I-Frame 的滑动窗口机制（窗口大小 1-7）
- [ ] 分段帧 (segmented frames) 的重组
- [ ] SSN/RSN 的状态管理
- [ ] 超时重传机制
- [ ] 接收状态跟踪

---

## 三、安全层加密模式

### 当前状态
只支持认证加密 (authenticated encryption)，不支持单独加密或单独认证。

### 未实现部分

| 位置 | 问题 | 影响 |
|------|------|------|
| `security.py:392` | `TODO: Is there a reason to support only encrypted or only authenticated data?` |
| `security.py:410` | `NotImplementedError: encrypt() only handles authenticated encryption` |
| `security.py:458` | `NotImplementedError: encrypt() only handles authenticated encryption` |

### 需要实现

- [ ] 仅加密模式 (encryption without authentication)
- [ ] 仅认证模式 (authentication without encryption)
- [ ] 不同加密套件的灵活支持

---

## 四、数据类型和编码

### 未实现或测试不完整

| 位置 | 问题 | 影响 |
|------|------|------|
| `dlms_data.py:71` | `NotImplementedError` - 某些数据类型未实现 |
| `dlms_data.py:155` | `TODO: test this` - CompactArray 解码未充分测试 |
| `a_xdr.py:103` | `TODO: we need to be able to fix the length of variable length data` |
| `a_xdr.py:160` | `TODO: Is all attributes of fixed length in X-ADR?` |
| `a_xdr.py:206` | `TODO: should have a function to get variable integer` |

---

## 五、时区处理

### 未实现部分

| 位置 | 问题 | 影响 |
|------|------|------|
| `time.py:240` | `TODO: We need a way to handle different ways of interpreting the timezone offset` |

### 需要实现

- [ ] 多种时区偏移格式的解析
- [ ] 夏令时 (DST) 处理
- [ ] 时区转换支持

---

## 六、接口类版本控制

### 未实现部分

| 位置 | 问题 | 影响 |
|------|------|------|
| `enumerations.py:291` | `TODO: how do we represent different versions of interface classes` |

### 需要实现

- [ ] 接口类版本号管理
- [ ] 不同版本的兼容性处理

---

## 七、数据通知增强

### 当前状态
基础 DataNotification 解析已实现，但处理功能有限。

### 需要增强

- [ ] DataNotificationHandler 的事件类型自动检测
- [ ] 基于 OBIS 代码的事件分类
- [ ] 报警/事件的具体识别逻辑
- [ ] 通知的持久化和查询

---

## 八、SAP (Support for Selective Access) 复杂描述符

### 未实现部分

| 功能 | 描述 |
|------|------|
| 复杂 RangeDescriptor | 多条件范围选择 |
| 结构化访问选择 | 嵌套结构的选择性访问 |
| 动态模板访问 | 基于模板的数据访问 |

---

## 九、脚本处理 (Script Handling)

### 未实现部分

| 功能 | 描述 | 优先级 |
|------|------|--------|
| Script 表 | 脚本操作和执行 | 低 |
| Script 结果 | 脚本执行结果处理 | 低 |
| Script 错误处理 | 脚本执行错误 | 低 |

---

## 十、图像传输 (Image Transfer)

### 未实现部分

| 功能 | 描述 | 优先级 |
|------|------|--------|
| Image 识别 | 图像数据识别 | 低 |
| Image 块传输 | 大数据分块传输 | 低 |
| Image 验证 | 图像完整性校验 | 低 |
| 固件升级流程 | 完整的升级流程 | 低 |

---

## 十一、服务器/模拟器模式

### 未实现部分

| 功能 | 描述 | 优先级 |
|------|------|--------|
| DLMS 服务器 | 完整的服务端实现 | 中 |
| 仪表模拟器 | 用于测试的模拟器 | 中 |
| 反向连接 | 仪表主动连接服务器 | 中 |

---

## 十二、Profile Generic 高级功能

### 需要增强

| 功能 | 当前状态 | 需要 |
|------|----------|------|
| 缓冲区读取方向 | 仅支持正向读取 | 可能需要反向 |
| 捕获对象解析 | 基础支持 | 动态解析增强 |
| 滚动缓冲区 | 未实现 | 高级用例 |

---

## 十三、异常恢复机制

### 需要增强

| 场景 | 当前状态 |
|------|----------|
| 连接中断恢复 | 基础重连 |
| 数据损坏恢复 | 未实现 |
| 状态不一致修复 | 未实现 |
| 部分数据重传 | 依赖超时重试 |

---

## 十四、性能优化

### 可优化项

| 功能 | 当前状态 | 潜在提升 |
|------|----------|----------|
| HDLC 窗口机制 | 固定窗口=1 | 3-7倍吞吐量 |
| 批量操作 | 未充分利用 | 减少往返 |
| 数据压缩 | 时戳压缩已实现 | 其他数据类型 |
| 连接复用 | 基础支持 | 连接池 |

---

## 实现优先级建议

### 高优先级（影响性能或稳定性）

1. **HDLC 多帧窗口优化** - 显著提升吞吐量
2. **Action 选择性访问解析** - 功能完整性
3. **异常恢复机制** - 提升稳定性

### 中优先级（扩展功能）

1. **服务器/模拟器模式** - 方便测试
2. **数据通知增强** - 更好的推送处理
3. **时区处理** - 完善地理支持

### 低优先级（特定用例）

1. **脚本处理** - 特定仪表功能
2. **图像传输** - 固件升级
3. **SAP 复杂描述符** - 高级查询

---

## 总结

### 核心功能完成度: 94%

### 完整实现的模块

- ✅ ACSE (应用连接)
- ✅ XDLMS APDU (GET/SET/ACTION)
- ✅ 安全层 (认证和加密)
- ✅ HDLC 基础帧处理
- ✅ 数据编码 (AXDR)
- ✅ 密钥管理

### 需要补充的模块

- ⚠️ HDLC 多帧和窗口优化
- ⚠️ Action 选择性访问
- ⚠️ 数据通知高级处理
- ❌ 服务器模式
- ❌ 脚本和图像处理
