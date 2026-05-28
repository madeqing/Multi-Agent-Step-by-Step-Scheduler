---
name: multi-agent-scheduler
description: |
  多智能体逐步调度 Skill（SQLite 版）—— 将复杂任务拆解为步骤，每步由 Dev 执行 + Tester 严格审查，通过才进下一步。
  核心变化：数据存储从 JSON 文件迁移到 SQLite，提供 task_ops.py 脚本进行任务管理，无需每次读取所有配置文件。
  触发条件：用户提到"多智能体调度"、"逐步完成"、"Dev+Tester"、"分步开发"、"任务管理"。
version: 2.2.0
platforms: [linux, macos, windows]
trigger:
  keywords:
    - 多智能体调度
    - 逐步完成
    - dev tester协作
    - 分步开发
    - 逐步审查
    - multi-agent
    - 任务分步
    - 逐步派发
    - dev tester
  scenarios:
    - 复杂任务需要多步骤审查
    - Dev + Tester 协作模式
    - 需要任务持久化和审计轨迹
    - 需要脱离 JSON 文件的数据管理
---

# Multi-Agent Scheduler — SQLite 版

> 多智能体逐步调度 Skill（SQLite 版）。  
> 数据存储从 JSON 文件迁移到 SQLite，不再每次读取所有配置文件。  
> 提供 `task_ops.py` 脚本进行所有任务管理操作。  

---

## 一、核心概念

### 1.1 角色职责

| 角色 | 职责 |
|------|------|
| **Leader（我）** | 拆步规划、派发任务、协调审查、状态管理 |
| **Dev（执行者）** | 接收任务、执行实现、修复 FAIL |
| **Tester（审查者）** | 严格验收、输出 PASS / FAIL、提供修复建议 |

### 1.2 数据存储

所有数据存储在 SQLite 数据库：`~/.hermes/multi-agent-scheduler.db`

**不再使用 JSON 文件存储任务数据**。JSON 文件仅用于：
- 任务 workspace 内的交付物（final.md、contra.html 等）
- role-map.json（角色契约映射，供 Dev/Tester 读取）

### 1.3 数据库表结构

| 表名 | 用途 |
|------|------|
| `tasks` | 主任务表 |
| `steps` | 步骤表（外键 → tasks） |
| `reviews` | 审查记录表（外键 → steps） |
| `active_task` | 当前激活任务（单行） |
| `event_log` | 事件审计日志 |

### 1.4 任务状态

```
task_status: running | paused | waiting_confirm | done
step_status:  pending | active | rework | passed | paused
```

### 1.5 步骤流程

```
Dev 执行 ──(complete)──→ Tester 审查 ──┬──(PASS)──→ 进入下一步
                                        └──(FAIL)──→ 打回 Dev 修复
```

## 二、脚本使用

所有任务管理操作通过 `scripts/task_ops.py` 完成。

### 2.1 初始化数据库

```bash
python3 scripts/task_ops.py init
# 或指定路径
python3 scripts/task_ops.py init --db-path /path/to/custom.db
```

> **注意**：`task_ops.py init` 不支持 `--verify`。如需仅验证数据库完整性，使用 `python3 scripts/init_db.py --verify`。

### 2.2 任务管理命令

```bash
# 列出所有任务
python3 scripts/task_ops.py list

# 查看任务详情
python3 scripts/task_ops.py show <task_id>

# 查看当前激活任务
python3 scripts/task_ops.py current

# 创建新任务
python3 scripts/task_ops.py create \
  --title "任务名称" \
  --root "/abs/path/to/task_root" \
  --original-prompt "原始需求描述" \
  --aliases "别名1" "别名2"

# 激活任务（设为当前任务）
python3 scripts/task_ops.py activate <task_id>

# 清除激活任务
python3 scripts/task_ops.py deactivate

# 导出 final.md（所有步骤 PASS 后必须执行）
python3 scripts/task_ops.py finalize <task_id>
```

### 2.3 步骤管理命令

```bash
# 为任务添加步骤
python3 scripts/task_ops.py step-add <task_id> "Step 1: 标题" \
  --goal "目标描述" \
  --ac "验收标准1" "验收标准2" \
  --allowed-files "/path/to/file1" \
  --owner dev

# 将步骤设为 active（开始执行）
python3 scripts/task_ops.py step-active <step_id>

# 更新步骤状态
python3 scripts/task_ops.py step-set <step_id> pending|active|rework|passed|paused

# 标记步骤完成（Tester 决策）
python3 scripts/task_ops.py step-done <step_id> --decision PASS|FAIL
```

### 2.4 审查记录命令

```bash
# 添加审查记录（每次 Tester 审查后）
python3 scripts/task_ops.py review-add <step_id> PASS|FAIL \
  --reason "审查理由" \
  --issue-count 2 \
  --issue-list "问题1" "问题2" \
  --fix-mode repair|redo \
  --can-proceed 0|1
```

### 2.5 事件日志

```bash
# 查看任务事件日志
python3 scripts/task_ops.py events <task_id>

# 记录自定义事件
python3 scripts/task_ops.py log <task_id> <event_type> "详情描述"
```

### 2.6 字段更新

```bash
# 更新任务字段
python3 scripts/task_ops.py task-set <task_id> <field> <value>

# 可更新字段：task_status | current_step_id | current_step_title |
#            current_step_status | final_artifact_path | final_export_path |
#            ready_for_user_confirm | role_map_version
```

### 2.7 导出 final.md（必须执行）

**所有步骤 PASS 后，必须执行此命令生成执行报告 final.md**，该文件是任务的正式交付物之一，包含完整执行过程、审查记录和审计日志。

```bash
# 导出完整执行报告到 task_root/final.md
python3 scripts/task_ops.py finalize <task_id>

# 指定输出路径（覆盖 task_root/final.md 默认值）
python3 scripts/task_ops.py task-set <task_id> final_export_path /custom/path/report.md
python3 scripts/task_ops.py finalize <task_id>
```

> **注意**：`finalize` 会自动将输出路径回写 `final_export_path` 字段到数据库。

## 三、工作流程（标准 8 步）

### Step 0: 环境检查

```bash
# 确认数据库存在并完整
python3 scripts/task_ops.py init

# 列出已有任务
python3 scripts/task_ops.py list
```

### Step 1: 分析需求

判断是否需要多步骤审查编排：
- 任务需要 2+ 个有序步骤
- 需要 Dev + Tester 协作
- 有失败返修循环
- 需要完整审计轨迹

### Step 2: 创建任务

```bash
python3 scripts/task_ops.py create \
  --title "项目X实现" \
  --root "/abs/path/to/project-x" \
  --original-prompt "原始需求描述" \
  --aliases "project-x" "px"
```

### Step 3: 规划并添加步骤

```bash
python3 scripts/task_ops.py step-add <task_id> "Step 1: 基础架构" \
  --goal "完成项目基础架构" \
  --ac "有项目结构文档" "有接口定义" \
  --allowed-files "/path/to/index.html" \
  --owner dev
# 对每个步骤重复调用 step-add（无需按顺序，后添加的步骤自动排到最后）
```

> **批量添加**：每个步骤单独调用一次 `step-add`，无需按顺序操作。步骤 ID 自动递增（S1, S2, …）。

### Step 4: 激活任务，开始第一步

```bash
python3 scripts/task_ops.py activate <task_id>
python3 scripts/task_ops.py step-active S1
```

> **顺序**：`activate` 先于 `step-active`。`activate` 设任务为 running 状态，`step-active` 才真正开始第一步执行。

### Step 5: Dev 执行，Tester 审查

Dev 完成任务后：

```bash
# Tester 通过
python3 scripts/task_ops.py step-done S1 --decision PASS
python3 scripts/task_ops.py review-add S1 PASS --reason "满足所有验收标准"

# Tester 不通过
python3 scripts/task_ops.py step-done S1 --decision FAIL
python3 scripts/task_ops.py review-add S1 FAIL \
  --reason "缺少XX功能" \
  --issue-count 1 \
  --issue-list "未实现YY功能" \
  --fix-mode repair
```

### Step 6: FAIL 处理

```
Tester 输出 FAIL
       │
       ▼
 记录失败原因（review-add）
       │
       ├─ delegate_task 派发 Dev 修复
       │       │
       │       ▼
       │  正常完成 → step-active 重新审查
       │
       └─ delegate_task 超时（修复点精确1-3文件）
               │
               ▼
         Leader 直接用 patch 介入（记录 leader_fallback 事件）
               │
               ▼
         通知用户发生了回退

同一步骤连续 4 次正式 FAIL → 暂停任务，通知用户决策
```

> 详见 6.2 节 `delegate_task` 超时时的 Leader 回退策略。

### Step 7: PASS 处理

```
所有步骤 PASS
       │
       ▼
 更新任务 final_artifact_path
       │
       ▼
 python3 scripts/task_ops.py task-set <task_id> task_status waiting_confirm
```

### Step 8: 导出 final.md + 清理

用户确认"没问题"后：

1. **导出 final.md 执行报告**（必须）：
   ```bash
   python3 scripts/task_ops.py finalize <task_id>
   ```
2. 清理 Kanban 任务记录（可选）
3. 用户自行保留或归档 workspace 中的 final.md 和交付物

> **final.md 包含内容**：任务概述、步骤执行摘要（含耗时）、每步详情（含审查记录）、事件审计日志。

## 四、任务检索顺序

用户只记得粗略名字时，按以下顺序匹配：

1. `task_id`（精确）
2. `task_title`（模糊匹配）
3. `aliases`（数组元素匹配）
4. `original_prompt` / `summary` / `keywords`

命中多个时：优先 `running` → `paused` → `waiting_confirm` → `updated_at` 最近。

## 五、FAIL 闭环规则

- **Leader** 只转发问题、拆解修复点、更新状态，不能修改 Dev 负责的文件
- **Tester** 只输出 PASS / FAIL，不参与修复
- **Dev** 是唯一执行修复的人
- 同一步骤连续 **4 次**正式 FAIL 后暂停任务，通知用户决策

## 六、陷阱与注意事项

### 6.1 `--verify` 参数的适用范围

- **`task_ops.py init`**：调用 `init_db()` 函数，不支持 `--verify` 参数
- **`scripts/init_db.py`**（直接调用）：支持 `--verify`，仅验证数据库完整性不修改

正确用法：
```bash
# task_ops.py — 初始化数据库
python3 scripts/task_ops.py init

# init_db.py — 仅验证（不修改）
python3 scripts/init_db.py --verify
```

### 6.2 `delegate_task` 超时时的回退策略

当 Dev 修复任务通过 `delegate_task` 派发时，如果遇到 Subagent 超时（尤其在修复小而精确的代码改动时），**Leader 应直接使用 `patch` 工具对目标文件进行修复**，而不是反复重试 delegate。

判定标准：
- 修复点精确、范围小（1-3 个函数/代码块）
- delegate_task 已超时一次
- 修复逻辑已由 Tester 分析清楚

回退后仍需记录事件日志，并通知用户发生了回退。

### 6.3 其他常见异常

| 场景 | 处理方式 |
|------|---------|
| 数据库文件不存在 | 自动创建（`init` 时），路径错误时用 `--db-path` 指定 |
| `step-active` 时任务未激活 | 提示先运行 `activate`，按正确顺序执行 |
| 步骤ID写错（如 `S0` 不存在） | `task_ops.py list` 查看实际步骤ID |
| `task-set` 更新了非法字段 | 查看命令帮助确认可用字段列表 |
| 用户要求跳过某步骤 | 不允许，FAIL 后修复继续，步骤不可跳过 |
| delegate_task 超时但修复范围大 | 不使用 fallback，继续重试 delegate 或暂停任务让用户决策 |

## 七、事件类型参考

| event_type | 含义 |
|-----------|------|
| `created` | 任务创建 |
| `step_added` | 步骤添加 |
| `step_started` | 步骤开始执行 |
| `step_paused` | 步骤暂停 |
| `review_pass` | Tester 审查通过 |
| `review_fail` | Tester 审查失败 |
| `resumed` | 任务重新激活 |
| `field_updated` | 任务字段更新 |
| `leader_fallback` | Leader 直接介入修复（delegate 超时回退） |
| `closed` | 任务关闭 |

## 八、与旧版（JSON 版）的区别

| | 旧版（JSON） | 新版（SQLite） |
|---|---|---|
| 数据存储 | JSON 文件 | SQLite 数据库 |
| 任务索引 | 无 | `tasks` 表 |
| 激活状态 | 无 | `active_task` 表 |
| 步骤存储 | 每个任务 `steps.json` | `steps` 表 |
| 审查记录 | `reviews/Sx.md` 文件 | `reviews` 表 |
| 审计日志 | 无 | `event_log` 表 |
| 每次查询 | 读取多个 JSON 文件 | 单次 SQL 查询 |
| 数据一致性 | 文件锁/写入冲突风险 | ACID 事务 |
| 历史记录 | 文件版本（手动） | 数据库内完整历史 |

## 九、脚本文件清单

```
multi-agent-scheduler/
├── SKILL.md                    # 本文件
├── scripts/
│   ├── init_db.py             # 数据库初始化
│   ├── task_ops.py            # 任务管理脚本（CRUD）
│   └── db_schema.py           # Schema 定义（参考）
├── dev.md                      # Dev 角色契约
├── tester.md                   # Tester 角色契约
├── leader.md                   # Leader 角色契约（参考）
├── workflow/
│   └── tasks/_template/       # 任务 workspace 模板
│       ├── plan.md
│       ├── status.json
│       ├── steps.json
│       ├── role-map.json
│       ├── dev/agents.md
│       ├── tester/agents.md
│       └── reviews/Sx.md
└── deliverables/              # 最终交付物归档
```

## 十、数据库路径

默认路径：`~/.hermes/multi-agent-scheduler.db`

可通过环境变量或 `--db-path` 参数覆盖：

```bash
export MULTI_AGENT_SCHEDULER_DB=/path/to/custom.db
```

## 十一、参考资料

- `references/finalize-workflow.md` — final.md 强制交付物工作流说明
