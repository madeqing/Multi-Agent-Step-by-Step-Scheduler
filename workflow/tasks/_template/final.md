# Final Artifact

## Task Meta
- task_id:
- task_title:
- aliases:
- original_prompt:
- task_root:
- role_map_version:
- final_artifact_path: workflow/tasks/{task_id}/final.md
- final_export_path: deliverables/{task_id}/final.md

## Final Status
- final_status:
- cleanup_status:
- user_confirmed:
- user_confirmation_required: true

## Deliverable Summary
- 

## Files Changed
- 

## Verification Summary
- 

## Notes
- 这是当前任务的最终产物。
- 只有当所有步骤通过审查后，才能写入或更新本文件。
- 用户确认“没问题”后，Leader 才能执行导出与清理。
- 清理完成后，该 task 必须从 `workflow/task-index.json` 删除，`workflow/active-task.json` 置空，避免配置膨胀。

## Cleanup Rule
1. 导出 `deliverables/{task_id}/final.md`
2. 从 `workflow/task-index.json` 删除该任务
3. 清空 `workflow/active-task.json`
4. 删除或冻结 `workflow/tasks/{task_id}/`