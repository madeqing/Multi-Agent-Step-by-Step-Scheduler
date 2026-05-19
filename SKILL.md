# Multi-Agent Scheduler — SQLite 版

> 多智能体逐步调度 Skill（SQLite 版）。  
> 数据存储从 JSON 文件迁移到 SQLite，不再每次读取所有配置文件。  
> 提供 `task_ops.py` 脚本进行所有任务管理操作。  

---
name: multi-agent-scheduler
description: |
  多智能体逐步调度 Skill（SQLite 版）—— 将复杂任务拆解为步骤，每步由 Dev 执行 + Tester 严格审查，通过才进下一步。
  核心变化：数据存储从 JSON 文件迁移到 SQLite，提供 task_ops.py 脚本进行任务管理，无需每次读取所有配置文件。
  触发条件：用户提到"多智能体调度"、"逐步完成"、"Dev+Tester"、"分步开发"、"任务管理"。
version: 2.0.0
platforms: [linux, macos, windows]
trigger:
  keywords:
    - 多智能体调度
    - 逐步完成
    - dev tester协作
    - 分步开发
    - 逐步审查
    - multi-agent
  scenarios:
    - 复杂任务需要多步骤审查
    - Dev + Tester 协作模式
    - 需要任务持久化和审计轨迹
    - 需要脱离 JSON 文件的数据管理
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
# 验证数据库完整性
python3 scripts/task_ops.py init --verify
```

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

## 三、工作流程（标准 8 步）

### Step 0: 环境检查

```bash
# 确认数据库存在并完整
python3 scripts/task_ops.py init --verify

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
  --original-prompt "用户原始需求" \
  --aliases "project-x" "px"
```

### Step 3: 规划并添加步骤

```bash
python3 scripts/task_ops.py step-add <task_id> "Step 1: 基础架构" \
  --goal "完成项目基础架构" \
  --ac "有项目结构文档" "有接口定义" \
  --allowed-files "/path/to/index.html" \
  --owner dev
# 重复添加所有步骤...
```

### Step 4: 激活任务，开始第一步

```bash
python3 scripts/task_ops.py activate <task_id>
python3 scripts/task_ops.py step-active S1
```

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
       ▼
 Dev 修复 → step-active S1 → 重新审查
       │
       ▼
 同一步骤 4 次 FAIL → 暂停任务，通知用户
```

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

### Step 8: 清理

用户确认"没问题"后：

```bash
python3 scripts/task_ops.py task-set <task_id> task_status done
python3 scripts/task_ops.py deactivate
# workspace 文件（final.md 等）由用户自行保留或归档
```

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

## 六、事件类型参考

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
| `closed` | 任务关闭 |

## 七、与旧版（JSON 版）的区别

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

## 八、脚本文件清单

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

## 九、数据库路径

默认路径：`~/.hermes/multi-agent-scheduler.db`

可通过环境变量或 `--db-path` 参数覆盖：

```bash
export MULTI_AGENT_SCHEDULER_DB=/path/to/custom.db
```
