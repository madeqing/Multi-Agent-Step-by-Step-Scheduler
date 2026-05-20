# multi-agent-scheduler vs kanban-scheduler

## 核心对比

| | multi-agent-scheduler（JSON版） | kanban-scheduler（Kanban版） |
|---|---|---|
| **状态存储** | JSON 文件（`workflow/` 目录） | Kanban SQLite DB（`~/.hermes/kanban.db`） |
| **派发机制** | `delegate_task` subagent | `kanban_create` + dispatcher spawn |
| **持久性** | 依赖文件存活，context 压缩后可能丢失 | SQLite 持久，永不丢失 |
| **任务可见性** | JSON 文件，本地读写 | 任何 profile 或人都可以读写任务 |
| **人工介入** | `waiting_confirm` 后人工确认 | 任意节点 `kanban_block(reason=...)` |
| **失败恢复** | 读取 JSON 续跑 | `kanban_show()` 读取 prior attempts |
| **审计轨迹** | 本地文件 | SQLite 完整事件日志 |
| **适用场景** | 快速验证、单次多步骤任务 | 长期任务、跨会话、需完整审计 |

## 共同的核心编排原则

无论选哪个，都遵循相同原则：

1. **Leader 拆步**：把任务分解为最小可审查单元
2. **Dev 执行**：接收任务，执行实现
3. **Tester 审查**：逐项核验 acceptance criteria，输出 PASS 或 FAIL
4. **FAIL 打回 Dev**：只有 PASS 才推进下一步
5. **全部 PASS → final.md → 用户确认 → 清理**

## 选择决策树

```
任务需要 2+ 个有序步骤？
  │
  ├─ YES → 需要跨 session 持久化？
  │         ├─ YES → kanban-scheduler
  │         └─ NO → 两者皆可
  │              ├─ 步骤少、快速 → multi-agent-scheduler
  │              └─ 步骤多、需审计 → kanban-scheduler
  │
  └─ NO → delegate_task 或直接回答
```

## WSL 环境下的路径注意

两个 skill 在 WSL 下都使用绝对路径：
- `multi-agent-scheduler`：`/home/asus/.hermes/skills/multi-agent-scheduler/workflow/tasks/{task_id}/`
- `kanban-scheduler`：使用 `$HERMES_KANBAN_WORKSPACE`，由 dispatcher 自动设置
