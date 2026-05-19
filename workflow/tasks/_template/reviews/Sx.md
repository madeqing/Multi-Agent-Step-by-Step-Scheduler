# Step {{step_id}} Review Record

> 由 Tester 产出、Leader 落盘。
> 每次正式审查都追加一个 Attempt block，不覆盖历史记录。
> `issue_list` 是强制字段：PASS 也必须填写；若无问题，写 `issue_count: 0` 且 `- none`。
> 审查标准 = 当前 step packet + Dev 契约 + 共享约束 + Tester 自身审查规则。
> 证据尽量指向可复现材料：文件路径、行号、截图、日志、命令输出、接口响应等。

## 1. Task Meta
- task_id:
- task_title:
- aliases:
- original_prompt:
- task_root:
- role_map_version:

## 2. Step Snapshot
- task_id:
- task_title:
- aliases_snapshot:
- original_prompt_excerpt:
- task_root:
- step_id:
- title:
- task_status:
- step_status:
- attempts_total:
- final_artifact_path:
- final_export_path:
- dev_contract:
  - agents:
  - soul:
- tester_policy:
  - agents:
  - soul:

## 3. Severity Definitions
- blocker: 会导致任务不可用、不可交付、错误、危险、严重错用、无法验收
- major: 会显著降低质量、稳定性、体验、维护性、交接性、可信度
- minor: 不影响交付，但建议优化
- nit: 纯风格或极轻微偏好，原则上不作为 FAIL 依据

## 4. Decision Rules
- PASS：无 blocker，且无会阻塞交付的 major 问题；minor / nit 可记录
- FAIL：存在 blocker 或 major，或证据不足以放心交付
- 只要问题会影响真实使用、后续维护、交接、体验、稳定性、安全性、合规性、可验证性，就优先挑出来
- 但所有 FAIL 都必须有证据，不得纯主观判死刑
- PASS 不代表“没问题”，只代表“没有阻塞交付的重大问题”

## 5. Review Coverage Checklist
- [ ] 正确性
- [ ] 完整性
- [ ] 一致性
- [ ] 鲁棒性
- [ ] 边界处理
- [ ] 异常处理
- [ ] 恢复能力
- [ ] 安全性
- [ ] 性能与资源消耗
- [ ] 可读性
- [ ] 可维护性
- [ ] 可扩展性
- [ ] 可交接性
- [ ] 可验证性
- [ ] 可观测性
- [ ] 易用性
- [ ] 可操作性
- [ ] 兼容性
- [ ] 合规性
- [ ] 体验质量
- [ ] 交付可信度

## 6. Attempt {{n}}
- review_time:
- reviewer: tester
- review_basis:
  - step packet:
  - dev agents:
  - dev soul:
  - shared constraints:
- reviewer_policy_reference:
  - tester agents:
  - tester soul:
- dev_submission_summary:
  - modified_files:
  - implementation_summary:
  - verification_method:
  - known_risks:
- checks_performed:
  - contract compliance:
  - scope boundary:
  - acceptance criteria:
  - coverage / edge cases:
  - tests / static review:
  - regression / side effects:
- conclusion: PASS / FAIL
- basis:
- reason:
- fix_mode: repair / redo
- need_recheck:
- can_proceed:

### issue_list
- issue_count:

> 若无问题，写 `- none`，并将 `issue_count` 设为 `0`

#### Issue 1
- category:
- severity: blocker / major / minor / nit
- evidence:
- impact:
- fix_suggestion:
- recheck_required:
- related_files:

#### Issue 2
- category:
- severity: blocker / major / minor / nit
- evidence:
- impact:
- fix_suggestion:
- recheck_required:
- related_files:

#### Issue 3
- category:
- severity: blocker / major / minor / nit
- evidence:
- impact:
- fix_suggestion:
- recheck_required:
- related_files:

### Review Notes
- summary:
- next_action:
- notes:

## 7. Final Outcome
- final_result:
- total_attempts:
- step_closed:
- if_failed_pause_reason:
- next_action:

## 8. Final Step Extra（仅最终步骤填写）
- final_artifact_path:
- final_export_path:
- ready_for_user_confirm:
- user_confirmation_needed: