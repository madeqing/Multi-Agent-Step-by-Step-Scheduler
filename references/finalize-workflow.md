# multi-agent-scheduler finalize 工作流

## final.md 是强制交付物

`multi-agent-scheduler` v2.2.0 起，**final.md 执行报告是强制交付物**，不是可选的。

### 正确流程

```
所有步骤 PASS
    ↓
task-set <task_id> task_status waiting_confirm
    ↓
finalize <task_id>        ← 生成 final.md
    ↓
用户确认"没问题"
    ↓
task-set <task_id> task_status done
deactivate
```

### finalize 命令输出内容

- 任务概述（创建时间、状态、最终产物路径）
- 步骤执行摘要表（含耗时）
- 每步详情（goal、验收标准、审查记录含 issue 列表）
- 事件审计日志（完整时间线）

### 优先级说明

之前 final.md 生成规则分散在文档各处，没有强制约束。v2.2.0 通过 `finalize` 命令将强制要求固化为流程。
