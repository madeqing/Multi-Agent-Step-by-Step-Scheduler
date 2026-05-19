# log.md（全维严苛挑刺版）

## 0. 记录约定
- append_only: yes
- history_mutation: no
- machine_source_of_truth: status.json
- human_audit_trail: log.md
- current_snapshot_is_current_state_only: yes
- history_kept_in:
  - Step Ledger
  - Event Timeline
  - Review Record
- step_ledger_purpose: step 高层摘要
- event_timeline_purpose: 原子事件历史
- review_record_purpose: 证据化审查历史
- review_block_contract: identical to reviews/Sx.md
- issue_list_policy: mandatory
- issue_list_field_order: category -> severity -> evidence -> impact -> fix_suggestion -> recheck_required -> related_files
- severity_policy: blocker / major / minor / nit
- evidence_preference: file path / line number / screenshot / log / command output / api response / recording
- if_no_issue_write:
  - issue_count: 0
  - issue_list: - none

## 1. Task Meta
- task_id:
- task_title:
- aliases:
- original_prompt:
- task_root:
- role_map_version:
- log_version: v3
- created_at:
- updated_at:

## 2. Current Snapshot
- task_status: created / running / blocked / waiting_review / waiting_confirm / closed
- current_phase: planning / implementation / review / confirmation / export / closure
- current_step_id:
- current_step_title:
- current_step_status:
- current_owner:
- last_event_id:
- last_event_time:
- last_review_time:
- last_review_result:
- last_review_issue_count:
- open_blockers:
- current_risks:
- pending_questions:
- final_artifact_path:
- final_export_path:
- ready_for_user_confirm:
- user_confirmation_needed:

## 3. Step Ledger（按 step 追加，高层摘要）
> 一步一条；每次 step 状态变化都追加，不覆盖历史。
> status: pending / running / blocked / reviewed / fixed / passed / failed / done
> decision: proceed / repair / redo / hold / close

### Step {{step_id}} Ledger
- step_id:
- title:
- owner:
- goal:
- inputs:
- constraints:
- expected_output:
- status:
- started_at:
- finished_at:
- packet_ref:
  - step_packet:
  - dev_contract:
  - review_packet:
- implementation_summary:
- review_summary:
- decision:
- known_risks:
- follow_up:
- related_files:
- review_ref:

### Step {{step_id}} Ledger
- step_id:
- title:
- owner:
- goal:
- inputs:
- constraints:
- expected_output:
- status:
- started_at:
- finished_at:
- packet_ref:
  - step_packet:
  - dev_contract:
  - review_packet:
- implementation_summary:
- review_summary:
- decision:
- known_risks:
- follow_up:
- related_files:
- review_ref:

> 如需更多 step，继续追加相同结构的 Step Ledger。

## 4. Event Timeline（按时间追加，原子事件）
> 记录所有关键动作、状态变化、调度、回退、确认、导出、关闭等。
> actor: leader / dev / tester / user / system
> event_type: task_create / task_resume / step_dispatch / dev_update / tester_review / leader_decision / user_confirm / pause / resume / rollback / export / close / cleanup / other
> scope: task / step / review / workspace / export / user / other

### Event {{event_id}}
- time:
- actor:
- event_type:
- step_id:
- scope:
- status_before:
- status_after:
- summary:
- details:
- evidence:
- related_files:
- blockers:
- next_action:
- remarks:

### Event {{event_id}}
- time:
- actor:
- event_type:
- step_id:
- scope:
- status_before:
- status_after:
- summary:
- details:
- evidence:
- related_files:
- blockers:
- next_action:
- remarks:

> 如需更多事件，继续追加相同结构的 Event Timeline。

## 5. Review Record（与 reviews/Sx.md 同构）
> 由 Tester 产出，Leader 落盘到 log.md。
> 每次正式审查都追加一个 Attempt block，不覆盖历史记录。
> `issue_list` 是强制字段：PASS 也必须填写；若无问题，写 `issue_count: 0` 且 `- none`。
> 审查标准 = 当前 step packet + Dev 契约 + 共享约束 + Tester 自身审查规则。
> 证据尽量指向可复现材料：文件路径、行号、截图、日志、命令输出、接口响应、录屏等。

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
- category: （如 correctness / completeness / ux / api_contract / security / performance / maintainability / observability / compatibility / compliance / other）
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

> 如需更多问题，继续追加 Issue 4 / Issue 5 / ...

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

## 6. Closure Snapshot
- task_closed: yes / no
- final_step_id:
- final_result:
- closed_at:
- closure_reason:
- final_artifact_path:
- final_export_path:
- ready_for_user_confirm:
- user_confirmation_needed:
- remaining_risks:
- archive_location:
- notes:

## 7. Append Rules
- 新事件一律追加到 Event Timeline
- 新步骤一律追加 Step Ledger
- 新审查一律追加 Review Record 的 Attempt block
- 不回写历史，不删旧记录，不改旧结论
- 如需更正，使用补充事件 / 补充审查 / 追加说明的方式完成
- 若 review 结论变化，保留旧结论并追加新 Attempt 说明原因
- 若 log 与实际 workspace 不一致，以最新可验证证据为准，并记录冲突事件
- Task Meta / Current Snapshot 只保留当前态，历史变更必须通过 Event Timeline / Review Record 留痕
