# Multi-Agent-Step-by-Step-Scheduler

多智能体逐步调度 Skill — 适用于 leader/dev/tester 协作的多步骤任务。

## 核心原则

- 先识别任务，再决定恢复或新建
- `workflow/active-task.json` 与 `workflow/task-index.json` 只保存未完成任务
- 每个任务拥有独立 workspace
- 一步一审，只有 PASS 才推进
- 同一步骤连续 4 次正式 FAIL 后暂停
- 全部步骤完成后生成 `final.md`
- 用户确认没问题后清理任务记录，防止配置膨胀

## 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 主 Skill 说明文档 |
| `leader.md` | Leader 角色说明 |
| `dev.md` | Dev 角色说明 |
| `tester.md` | Tester 角色说明 |
| `workflow/` | 工作流状态与模板 |
| `references/` | 参考文档 |

## 详细文档

见 [Hermes Agent Skills](https://hermes-agent.nousresearch.com/docs/)。
