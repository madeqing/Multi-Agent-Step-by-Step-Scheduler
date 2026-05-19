# 多智能体逐步调度 Skill

> 适用于 leader / dev / tester 协作的多步骤任务。  
> 核心原则：先识别任务，再决定恢复或新建；`workflow/active-task.json` 与 `workflow/task-index.json` 只保存未完成任务；每个任务拥有独立 workspace；一步一审；只看当前步骤；只有 PASS 才推进；同一步骤连续 4 次正式 FAIL 后暂停；全部步骤完成后生成 `final.md`；用户确认没问题后清理任务记录，防止配置膨胀。  
> 所有路径均使用仓库相对路径。

## 1. 适用场景
当任务需要拆步、依赖管理、dev/tester 协作、失败返修、回退、暂停、复盘、最终产物与确认后清理时，启用本 Skill。

## 2. 核心原则
- `task_id` 是机器主键，`task_title / aliases / original_prompt` 是人类检索字段。
- 人类展示统一用：`task_title [task_id]`。
- 新任务必须拥有独立 workspace。
- 切换任务前必须先落盘当前任务状态。
- Leader 负责调度，不负责代修。
- Tester 负责判定，不负责修复。
- Dev 负责实现与返修。
- `FAIL` 不是终点，而是回到 Dev 的返修信号。
- 所有步骤 PASS 之后才生成 `final.md`。
- 用户明确确认“没问题”之后才清理 task 记录，避免配置膨胀。
- 只有 Tester 可以给出 PASS / FAIL，Leader 不能替代 Tester 判定。

## 3. 任务识别与检索顺序
用户只记得粗略名字时，按以下顺序匹配：
1. `task_id`
2. `task_title`
3. `aliases`
4. `original_prompt / summary / keywords`
5. `status + updated_at`

如果命中多个候选：
- 优先 `running`
- 其次 `paused`
- 再按 `waiting_confirm`
- 然后按 `updated_at` 最近
- 仍不唯一时，列候选让用户选，不要猜

## 4. 任务隔离规则
- 全局只保留 `workflow/active-task.json` 与 `workflow/task-index.json`
- 每个任务都有独立 workspace：`workflow/tasks/{task_id}/`
- 不同任务之间不得共享可写 workflow 文件
- 旧任务默认保留到用户确认并清理为止
- 新任务不得覆盖旧任务 workspace
- `task_title` 改名时，旧标题必须追加进 `aliases`

## 5. 标准流程
1. 读取 active-task 与 task-index
2. 判断是续作还是新建
3. 恢复或创建 task workspace
4. 更新 active-task 与 task-index
5. 在当前 task workspace 中发现并绑定 dev/tester 角色契约
6. 写入 role-map / plan / steps / status / log
7. 只向 Dev 发送当前 step packet
8. Dev 完成后，Leader 组织 Tester 审查
9. Tester 输出 PASS / FAIL
10. 若 PASS：记录通过，进入下一步
11. 若 FAIL：
    - `step_status = rework`
    - `attempts += 1`
    - Leader 只整理失败原因与修复/重做指令
    - Leader 不得直接修改 Dev 负责的实现文件
    - Leader 将指令退回 Dev
12. Dev 按指令修复或重做后重新提交 Tester
13. 若同一步骤连续 4 次正式 FAIL，则暂停任务并通知用户
14. 全部步骤 PASS 后生成 `final.md`
15. `final.md` 完成后进入 `waiting_confirm`
16. 等待用户确认“没问题”
17. 用户确认后，导出 final 产物并清理 task 记录
18. 从 task-index 移除该 task，active-task 置空，workspace 可删除或冻结归档

## 6. FAIL→Dev 返修闭环
- Leader 只能转发问题、拆解修复点、更新状态，不能亲自修改 Dev 负责的实现文件
- 如果 FAIL 原因是实现缺陷：交给 Dev 修复
- 如果 FAIL 原因是当前步骤设计错误：Leader 可重拆当前步骤或调整 step 定义，但实现仍由 Dev 完成
- 如果 FAIL 原因是需求歧义：Leader 先澄清再继续，不得代写实现
- Tester 只输出判定与修复建议，不参与修复
- Dev 是唯一执行修复的人

## 7. packet 规范
### step packet 必须包含
- `task_id`
- `task_title`
- `aliases`
- `original_prompt`
- `task_root`
- `step_id`
- `title`
- `goal`
- `allowed_files`
- `acceptance_criteria`
- `constraints`
- `dependencies`
- `role_map_version`
- `fix_mode`（可选，`repair` / `redo`）

### review packet 必须包含
- `task_id`
- `task_title`
- `aliases`
- `original_prompt`
- `task_root`
- `step_id`
- `title`
- `dev_modified_files`
- `implementation_summary`
- `verification_method`
- `known_risks`
- `role_map_version`
- `required_fixes`
- `fix_mode`（FAIL 时建议填写 `repair` / `redo`）
- 若是最终步骤，还应包含 `final_artifact_path`、`final_export_path`

## 8. 状态定义
- `task_status`: `running` / `paused` / `waiting_confirm` / `done`
- `step_status`: `pending` / `active` / `rework` / `passed` / `paused`
- `final_status`: `draft` / `ready_for_confirm` / `confirmed`
- `cleanup_status`: `none` / `pending` / `complete`
- `attempts`: 只统计正式提交给 Tester 的轮次

## 9. 终态与清理
- `final.md` 是当前任务的最终产物
- 所有步骤 PASS 后才写 `final.md`
- `final.md` 生成后，task_status 进入 `waiting_confirm`
- 只有用户明确确认“没问题”后，才允许清理
- 清理顺序：
  1. 导出 `deliverables/{task_id}/final.md`
  2. 从 `workflow/task-index.json` 删除该 task
  3. 将 `workflow/active-task.json` 置空
  4. 删除或冻结 `workflow/tasks/{task_id}/`
- 清理完成后，该 task 不再出现在索引中，防止配置文件持续膨胀
- 如果用户要求修改 final.md，则不能清理，需回到 Dev / Tester 闭环继续返修

## 10. 暂停规则
- 同一步骤连续 4 次正式 FAIL 后暂停
- 暂停时必须说明：
  - 卡住的步骤
  - 4 次错误
  - 最可能根因
  - 下一步建议（继续 / 拆分 / 补充信息 / 重启）

## 11. 兼容模式
- 不支持文件写入：在对话中按文件路径输出
- 不支持 agent 间直连：由 Leader 转发
- 如果未发现 dev/tester 子 agent 且当前任务需要多角色协作，先暂停并请求用户确认是否有对应的子agent角色，若没有是否需要创建子agent，不需要则停止该skill执行任务


## 12. 路径解析与 WSL 环境注意事项
- **WSL 环境下 subagent 的 cwd 默认是 `/mnt/d/OpenClaw/skill`**，相对路径会相对于该目录解析
- **派发 delegate_task 时，`task_root` 必须使用绝对路径**，禁止传递相对路径
- 错误示例：`task_root: "workflow/tasks/snake-game-001"` → dev subagent 可能写到 `/mnt/d/OpenClaw/skill/workflow/tasks/...`
- 正确示例：`task_root: "/home/asus/.hermes/skills/multi-agent-scheduler/workflow/tasks/snake-game-001"`
- 验证方式：文件写入后立即检查文件是否出现在预期绝对路径，如出现在其他路径说明派发时路径有误
- 建议在 step packet 中显式注明文件绝对路径，如：
  ```
  文件位置：`/home/asus/.hermes/skills/multi-agent-scheduler/workflow/tasks/{task_id}/snake.html`