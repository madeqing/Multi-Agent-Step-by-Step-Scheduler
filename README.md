# Multi-Agent-Step-by-Step-Scheduler

多智能体逐步调度 Skill（SQLite 版）—— 将复杂任务拆解为步骤，每步由 Dev 执行 + Tester 严格审查，通过才进下一步。

## 核心变化（v2.x）

- 数据存储从 JSON 文件迁移到 **SQLite 数据库**（`~/.hermes/multi-agent-scheduler.db`）
- 所有任务管理操作通过 `task_ops.py` 脚本完成，无需手动读写 JSON
- 提供完整的**事件审计日志**
- **步骤不可跳过**，FAIL 后修复继续，只有 PASS 才推进下一步
- 同一步骤连续 **4 次**正式 FAIL 后暂停，通知用户决策

## 角色职责

| 角色 | 职责 |
|------|------|
| **Leader** | 拆步规划、派发任务、协调审查、状态管理 |
| **Dev** | 接收任务、执行实现、修复 FAIL |
| **Tester** | 严格验收，输出 PASS / FAIL，提供修复建议 |

## 快速开始

```bash
# 初始化数据库
python3 scripts/task_ops.py init

# 创建任务
python3 scripts/task_ops.py create \
  --title "项目X实现" \
  --root "/abs/path/to/project-x" \
  --original-prompt "原始需求描述" \
  --aliases "project-x" "px"

# 添加步骤
python3 scripts/task_ops.py step-add <task_id> "Step 1: 标题" \
  --goal "目标描述" \
  --ac "验收标准1" "验收标准2" \
  --owner dev

# 激活任务并开始第一步
python3 scripts/task_ops.py activate <task_id>
python3 scripts/task_ops.py step-active S1

# Tester 审查
python3 scripts/task_ops.py step-done S1 --decision PASS|FAIL

# 任务完成后导出报告
python3 scripts/task_ops.py finalize <task_id>
```

## 完整工作流程

```
Step 0: 环境检查（init + list）
Step 1: 分析需求（判断是否需要多步骤编排）
Step 2: 创建任务（create）
Step 3: 规划并添加步骤（step-add）
Step 4: 激活任务，开始第一步（activate + step-active）
Step 5: Dev 执行，Tester 审查（PASS/FAIL 循环）
Step 6: FAIL 处理（delegate 修复 或 leader_fallback）
Step 7: 所有 PASS → task_status = waiting_confirm
Step 8: finalize + 清理
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 主 Skill 说明文档（完整规范） |
| `scripts/task_ops.py` | 任务管理脚本（CRUD + 审查记录） |
| `scripts/init_db.py` | 数据库初始化 |
| `scripts/db_schema.py` | Schema 定义（参考） |
| `leader.md` | Leader 角色契约 |
| `dev.md` | Dev 角色契约 |
| `tester.md` | Tester 角色契约 |
| `references/` | 参考文档 |

## 详细文档

见 [Hermes Agent Skills](https://hermes-agent.nousresearch.com/docs/)。
