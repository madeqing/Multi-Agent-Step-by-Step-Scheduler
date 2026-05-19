# Multi-Agent-Scheduler 演示模式参考

本文件记录"演示模式"的工作流构造方法，用于用户要求"展示 FAIL 流程"、"看多轮打回"等场景。

## 演示模式的核心原则

- **Dev 代码必须真实**：即使演示 FAIL，dev 生成的代码仍需是真实可用的
- **审查结果可以构造**：为了展示完整的问题解决过程，审查报告可以按需构造 FAIL 场景
- **状态流转必须真实**：`step_status`、`consecutive_fails` 等必须真实更新到状态文件
- **必须至少一轮 PASS**：只有最终 PASS 才能推进下一步

## 演示模式的工作流构造

### Step-1：构造初始实现

使用 `delegate_task` 让 dev subagent 真实生成代码（这些代码在后续真实审查中会用到）。

### Step-2：构造审查记录

在 `reviews/Sx.md` 中预先写入各轮审查结果：

```markdown
## Step-X 审查报告（Round 1 → FAIL）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| xxx | FAIL | 原因... |

**总体结论: FAIL**

**问题汇总：**

1. **问题描述**
2. ...

---

## Step-X 审查报告（Round 2 → FAIL）

...
---

## Step-X 审查报告（Round N → PASS ✅）
```

### Step-3：更新状态文件

每次 FAIL 后真实更新：
- `status.json`：`step_status: "rework"`, `consecutive_fails += 1`
- `active-task.json`：当前 step 更新
- `task-index.json`：当前 step 更新

### Step-4：真实生成最终交付物

当最终 PASS 后，`final.md` 和实际产物文件必须真实存在。

## 构造多轮 FAIL 场景的建议

### Round 分配策略

| Round | 典型角色 | 适合展示的问题类型 |
|-------|---------|-----------------|
| R1 | 常规功能缺失 | 缺少核心字段/表/接口 |
| R2 | 细节遗漏 | 约束条件不满足、边界 case |
| R3 | 跨模块一致性问题 | 多文件联动时的不一致 |
| R4 | 极端 case | 性能、安全、容错 |

### 常见 FAIL 问题类型（便于构造）

**数据模型类**：
- 缺少必需的字段（外键、索引、默认值）
- 字段类型错误（BOOLEAN→ENUM）
- 约束缺失（UNIQUE、FOREIGN KEY）

**接口设计类**：
- 缺少接口（refresh token、修改密码）
- 字段命名不一致（is_accessible vs connection_status）
- 分页参数缺失

**实现质量类**：
- 变量名笔误（result.connection_status 应为 r.connection_status）
- 硬编码值（密码明文、magic number）
- 异常处理缺失

**约束违反类**：
- 依赖外部库（要求纯标准库却 import requests）
- 验收标准未满足（超时未设置、并发超限）

## 模拟演示的边界

**可以构造**：
- 审查报告中的 PASS/FAIL 结论
- FAIL 的具体问题描述
- 各轮次的问题清单

**不可以构造**：
- Dev 交付的代码（必须真实）
- 状态文件的真实更新
- 最终产物（final.md、交付物文件）

**反例（禁止）**：写 `simulate_deploy.py` 用 `print("[DEV] 执行启动...")` 假装调度过程。

**正例（必须）**：创建真实 workspace，通过 `delegate_task` 派发 Dev subagent，subagent 真实执行 `python3 app.py` 并返回结果。

## 示例：port-scanner-001 的 4 轮 FAIL

```
step-1: 需求分析
  R1 FAIL: 缺少 audit_logs、refresh token、is_accessible 语义
  R2 FAIL: 防抖动逻辑未体现、导出格式未明确
  R3 FAIL: 配置参数缺 2 项
  R4 FAIL: 健康检查机制缺失
  PASS

step-2: 扫描模块
  R1 FAIL: L404 变量名错误
  PASS

step-3: 数据库脚本
  R1 FAIL: 6个问题（密码明文、索引缺失、ENGINE未指定...）
  R2 FAIL: 3个问题（外键缺失、防抖参数、加密）
  PASS
```
