#!/usr/bin/env python3
"""
task_ops.py — multi-agent-scheduler SQLite 任务管理脚本

用法:
  python3 task_ops.py <command> [options]

命令:
  init                                    初始化数据库
  list                                    列出所有任务
  show <task_id>                          显示任务详情
  current                                 显示当前激活任务
  create --title TEXT --root PATH [opts]   创建新任务
  step-add <task_id> <step_title> [opts]  为任务添加步骤
  step-set <step_id> <status>             更新步骤状态
  step-active <step_id>                   将步骤设为 active
  step-done <step_id> --decision PASS|FAIL  标记步骤完成
  review-add <step_id> <PASS|FAIL> [opts] 添加审查记录
  activate <task_id>                      激活任务
  deactivate                              清除激活任务
  task-set <task_id> <field>=<value>      更新任务字段
  events <task_id>                         查看任务事件日志
  log <task_id> <event_type> [detail]     记录事件

数据导入:
  import-json <json_dir>                   从旧JSON目录导入任务

数据库:
  --db-path PATH                          指定数据库路径
"""

import argparse
import json
import os
import sqlite3
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Optional

# ---------------------------------------------------------------------------
# DB connection helper
# ---------------------------------------------------------------------------

DEFAULT_DB = Path.home() / ".hermes" / "multi-agent-scheduler.db"


def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    if not path.exists():
        print(f"ERROR: Database not found at {path}", file=sys.stderr)
        print("Run: python3 task_ops.py init", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def task_row(row: sqlite3.Row) -> dict:
    """Convert a task row to dict with parsed JSON columns."""
    d = dict(row)
    for col in ("aliases",):
        if d.get(col) and d[col] != "[]":
            try:
                d[col] = json.loads(d[col])
            except Exception:
                pass
    return d


def step_row(row: sqlite3.Row) -> dict:
    d = dict(row)
    for col in ("allowed_files", "acceptance_criteria", "constraints", "dependencies", "known_risks", "related_files"):
        if d.get(col) and d[col] != "[]":
            try:
                d[col] = json.loads(d[col])
            except Exception:
                pass
    return d


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def cmd_init(db_path: Optional[Path], force: bool = False):
    from init_db import init_db
    success = init_db(db_path or DEFAULT_DB, force=force)
    sys.exit(0 if success else 1)


# ---------------------------------------------------------------------------
# List tasks
# ---------------------------------------------------------------------------

def cmd_list(db_path: Optional[Path]):
    conn = get_db(db_path)
    rows = conn.execute(
        """SELECT task_id, task_title, task_status, current_step_title,
                  created_at, updated_at
           FROM tasks ORDER BY updated_at DESC"""
    ).fetchall()
    if not rows:
        print("No tasks found.")
        conn.close()
        return

    print(f"{'TASK_ID':<30} {'STATUS':<20} {'CURRENT_STEP':<30} {'UPDATED'}")
    print("-" * 100)
    for r in rows:
        step = (r["current_step_title"] or "—")[:28]
        print(f"{r['task_id']:<30} {r['task_status']:<20} {step:<30} {r['updated_at'][:10]}")
    conn.close()


# ---------------------------------------------------------------------------
# Show task
# ---------------------------------------------------------------------------

def cmd_show(task_id: str, db_path: Optional[Path]):
    conn = get_db(db_path)

    task = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    if not task:
        print(f"Task not found: {task_id}")
        conn.close()
        sys.exit(1)

    d = task_row(task)
    print(f"\n{'='*60}")
    print(f"Task: {d['task_title']} [{d['task_id']}]")
    print(f"Status: {d['task_status']}")
    print(f"Root: {d['task_root']}")
    print(f"Aliases: {d['aliases']}")
    print(f"Original prompt: {d['original_prompt'][:80]}...")
    print(f"Created: {d['created_at']}  Updated: {d['updated_at']}")
    print(f"Current step: {d['current_step_id']} / {d['current_step_title']} / {d['current_step_status']}")
    print(f"Ready for confirm: {d['ready_for_user_confirm']}")
    print(f"Final artifact: {d['final_artifact_path']}")
    print(f"Final export: {d['final_export_path']}")

    # Steps
    steps = conn.execute(
        "SELECT * FROM steps WHERE task_id = ? ORDER BY step_order",
        (task_id,)
    ).fetchall()
    print(f"\n--- Steps ({len(steps)}) ---")
    for s in steps:
        sd = step_row(s)
        print(f"  [{sd['step_id']}] {sd['title']}")
        print(f"    status={sd['status']}  attempts={sd['attempts']}  owner={sd['owner']}")
        print(f"    decision={sd['decision']}  started={sd['started_at'][:10] if sd['started_at'] else '—'}  finished={sd['finished_at'][:10] if sd['finished_at'] else '—'}")
        if sd['implementation_summary']:
            print(f"    impl: {sd['implementation_summary'][:60]}...")

    # Recent reviews
    reviews = conn.execute(
        """SELECT r.*, s.title as step_title
           FROM reviews r
           JOIN steps s ON r.step_id = s.step_id
           WHERE r.task_id = ?
           ORDER BY r.review_time DESC LIMIT 10""",
        (task_id,)
    ).fetchall()
    if reviews:
        print(f"\n--- Recent Reviews ---")
        for r in reviews:
            print(f"  [{r['step_title']}] {r['conclusion']}  {r['review_time'][:10]}  issues={r['issue_count']}")

    conn.close()


# ---------------------------------------------------------------------------
# Current task
# ---------------------------------------------------------------------------

def cmd_current(db_path: Optional[Path]):
    conn = get_db(db_path)
    row = conn.execute("SELECT * FROM active_task WHERE id = 1").fetchone()
    if not row or not row["task_id"]:
        print("No active task.")
        conn.close()
        return
    # Delegate to show
    conn.close()
    cmd_show(row["task_id"], db_path)


# ---------------------------------------------------------------------------
# Create task
# ---------------------------------------------------------------------------

def cmd_create(
    title: str,
    root: str,
    db_path: Optional[Path],
    original_prompt: str = "",
    aliases: list[str] | None = None,
):
    import uuid
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now = now_iso()

    conn = get_db(db_path)
    conn.execute(
        """INSERT INTO tasks
           (task_id, task_title, aliases, original_prompt, task_root,
            created_at, updated_at, task_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'running')""",
        (task_id, title, json.dumps(aliases or []), original_prompt, root, now, now),
    )
    # Log creation event
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, '', 'created', 'leader', ?, ?)",
        (task_id, f"Task created: {title}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Task created: {task_id}")
    print(f"  Title: {title}")
    print(f"  Root: {root}")
    print(f"  Run: python3 task_ops.py show {task_id}")


# ---------------------------------------------------------------------------
# Activate task
# ---------------------------------------------------------------------------

def cmd_activate(task_id: str, db_path: Optional[Path]):
    conn = get_db(db_path)
    task = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    if not task:
        print(f"Task not found: {task_id}")
        conn.close()
        sys.exit(1)

    now = now_iso()
    d = task_row(task)
    aliases_json = json.dumps(d["aliases"]) if isinstance(d["aliases"], list) else d["aliases"]
    conn.execute(
        """INSERT OR REPLACE INTO active_task
           (id, task_id, task_title, aliases, original_prompt, task_root,
            current_step_id, current_step_title, task_status, updated_at)
           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (task_id, d["task_title"], aliases_json, d["original_prompt"], d["task_root"],
         d["current_step_id"], d["current_step_title"], d["task_status"], now),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, '', 'resumed', 'leader', 'Task activated', ?)",
        (task_id, now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Task activated: {task_id} [{d['task_title']}]")


# ---------------------------------------------------------------------------
# Deactivate
# ---------------------------------------------------------------------------

def cmd_deactivate(db_path: Optional[Path]):
    conn = get_db(db_path)
    conn.execute("DELETE FROM active_task WHERE id = 1")
    conn.commit()
    conn.close()
    print("✓ Active task cleared.")


# ---------------------------------------------------------------------------
# Step add
# ---------------------------------------------------------------------------

def cmd_step_add(
    task_id: str,
    step_title: str,
    db_path: Optional[Path],
    goal: str = "",
    acceptance_criteria: list[str] | None = None,
    allowed_files: list[str] | None = None,
    constraints: list[str] | None = None,
    dependencies: list[str] | None = None,
    owner: str = "",
):
    import uuid
    conn = get_db(db_path)
    task = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    if not task:
        print(f"Task not found: {task_id}")
        conn.close()
        sys.exit(1)

    # Get next step_order
    max_order = conn.execute(
        "SELECT COALESCE(MAX(step_order), 0) FROM steps WHERE task_id = ?",
        (task_id,)
    ).fetchone()[0]
    step_id = f"S{max_order + 1}"
    now = now_iso()

    conn.execute(
        """INSERT INTO steps
           (step_id, task_id, step_order, title, goal, allowed_files,
            acceptance_criteria, constraints, dependencies, status,
            attempts, owner, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?)""",
        (step_id, task_id, max_order + 1, step_title, goal,
         json.dumps(allowed_files or []),
         json.dumps(acceptance_criteria or []),
         json.dumps(constraints or []),
         json.dumps(dependencies or []),
         owner, now, now),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, ?, 'step_added', 'leader', ?, ?)",
        (task_id, step_id, f"Step added: {step_title}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Step added: {step_id} [{step_title}]")


# ---------------------------------------------------------------------------
# Step set status
# ---------------------------------------------------------------------------

def cmd_step_set(step_id: str, status: str, db_path: Optional[Path]):
    valid = {"pending", "active", "rework", "passed", "paused"}
    if status not in valid:
        print(f"Invalid status. Must be one of: {valid}")
        sys.exit(1)

    conn = get_db(db_path)
    step = conn.execute("SELECT * FROM steps WHERE step_id = ?", (step_id,)).fetchone()
    if not step:
        print(f"Step not found: {step_id}")
        conn.close()
        sys.exit(1)

    now = now_iso()
    started_at = step["started_at"] or now if status == "active" else step["started_at"]
    conn.execute(
        "UPDATE steps SET status = ?, started_at = ?, updated_at = ? WHERE step_id = ?",
        (status, started_at, now, step_id),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, ?, ?, 'leader', ?, ?)",
        (step["task_id"], step_id, f"step_{status}", f"Step status -> {status}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Step {step_id} status -> {status}")


# ---------------------------------------------------------------------------
# Step active (set active + update task current_step)
# ---------------------------------------------------------------------------

def cmd_step_active(step_id: str, db_path: Optional[Path]):
    conn = get_db(db_path)
    step = conn.execute("SELECT * FROM steps WHERE step_id = ?", (step_id,)).fetchone()
    if not step:
        print(f"Step not found: {step_id}")
        conn.close()
        sys.exit(1)

    now = now_iso()
    conn.execute(
        "UPDATE steps SET status = 'active', started_at = COALESCE(started_at, ?), updated_at = ? WHERE step_id = ?",
        (now, now, step_id),
    )
    conn.execute(
        "UPDATE tasks SET current_step_id = ?, current_step_title = ?, current_step_status = 'active', updated_at = ? WHERE task_id = ?",
        (step_id, step["title"], now, step["task_id"]),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, ?, 'step_started', 'leader', ?, ?)",
        (step["task_id"], step_id, f"Step activated: {step['title']}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Step {step_id} is now active")


# ---------------------------------------------------------------------------
# Step done
# ---------------------------------------------------------------------------

def cmd_step_done(step_id: str, decision: str, db_path: Optional[Path]):
    if decision not in {"PASS", "FAIL"}:
        print("decision must be PASS or FAIL")
        sys.exit(1)

    conn = get_db(db_path)
    step = conn.execute("SELECT * FROM steps WHERE step_id = ?", (step_id,)).fetchone()
    if not step:
        print(f"Step not found: {step_id}")
        conn.close()
        sys.exit(1)

    now = now_iso()
    new_status = "passed" if decision == "PASS" else "rework"
    conn.execute(
        "UPDATE steps SET status = ?, decision = ?, finished_at = COALESCE(finished_at, ?), updated_at = ? WHERE step_id = ?",
        (new_status, decision, now, now, step_id),
    )
    conn.execute(
        "UPDATE tasks SET current_step_status = ?, updated_at = ? WHERE task_id = ?",
        (new_status, now, step["task_id"]),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, ?, ?, 'tester', ?, ?)",
        (step["task_id"], step_id, "review_pass" if decision == "PASS" else "review_fail",
         f"Tester decision: {decision}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Step {step_id} decision={decision} status={new_status}")


# ---------------------------------------------------------------------------
# Review add
# ---------------------------------------------------------------------------

def cmd_review_add(
    step_id: str,
    conclusion: str,
    db_path: Optional[Path],
    reason: str = "",
    issue_count: int = 0,
    issue_list: list[str] | None = None,
    fix_mode: str = "",
    can_proceed: int = 0,
    review_notes: dict | None = None,
):
    import uuid
    if conclusion not in {"PASS", "FAIL"}:
        print("conclusion must be PASS or FAIL")
        sys.exit(1)

    conn = get_db(db_path)
    step = conn.execute("SELECT * FROM steps WHERE task_id = ? AND step_id = ?", (step_id, step_id)).fetchone()
    if not step:
        step = conn.execute("SELECT * FROM steps WHERE step_id = ?", (step_id,)).fetchone()
    if not step:
        print(f"Step not found: {step_id}")
        conn.close()
        sys.exit(1)

    review_id = f"R{uuid.uuid4().hex[:8]}"
    now = now_iso()
    conn.execute(
        """INSERT INTO reviews
           (review_id, step_id, task_id, reviewer, review_time, conclusion,
            reason, fix_mode, can_proceed, issue_count, issue_list, review_notes, created_at)
           VALUES (?, ?, ?, 'tester', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (review_id, step_id, step["task_id"], now, conclusion, reason,
         fix_mode, can_proceed, issue_count,
         json.dumps(issue_list or []),
         json.dumps(review_notes or {}), now),
    )
    # Increment step attempts if FAIL
    if conclusion == "FAIL":
        conn.execute(
            "UPDATE steps SET attempts = attempts + 1, updated_at = ? WHERE step_id = ?",
            (now, step_id),
        )
    conn.commit()
    conn.close()
    print(f"✓ Review added: {review_id} for step {step_id} -> {conclusion}")


# ---------------------------------------------------------------------------
# Task set field
# ---------------------------------------------------------------------------

def cmd_task_set(task_id: str, field: str, value: str, db_path: Optional[Path]):
    allowed = {
        "task_status", "task_title", "current_step_id", "current_step_title",
        "current_step_status", "final_artifact_path", "final_export_path",
        "ready_for_user_confirm", "aliases", "role_map_version",
    }
    if field not in allowed:
        print(f"Field not allowed. Options: {allowed}")
        sys.exit(1)

    # Parse integer fields
    if field == "ready_for_user_confirm":
        value = "1" if value in ("1", "true", "yes") else "0"

    conn = get_db(db_path)
    now = now_iso()
    conn.execute(
        f"UPDATE tasks SET {field} = ?, updated_at = ? WHERE task_id = ?",
        (value, now, task_id),
    )
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, '', 'field_updated', 'leader', ?, ?)",
        (task_id, f"{field} -> {value}", now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Task {task_id}.{field} = {value}")


# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------

def cmd_events(task_id: str, db_path: Optional[Path]):
    conn = get_db(db_path)
    rows = conn.execute(
        "SELECT * FROM event_log WHERE task_id = ? ORDER BY created_at DESC",
        (task_id,)
    ).fetchall()
    if not rows:
        print(f"No events for {task_id}")
        conn.close()
        return
    print(f"{'TIME':<28} {'TYPE':<20} {'ACTOR':<10} {'DETAIL'}")
    print("-" * 80)
    for r in rows:
        print(f"{r['created_at']:<28} {r['event_type']:<20} {r['actor']:<10} {r['detail']}")
    conn.close()


# ---------------------------------------------------------------------------
# Log event
# ---------------------------------------------------------------------------

def cmd_log(task_id: str, event_type: str, db_path: Optional[Path], detail: str = ""):
    conn = get_db(db_path)
    now = now_iso()
    conn.execute(
        "INSERT INTO event_log (task_id, step_id, event_type, actor, detail, created_at) VALUES (?, '', ?, 'system', ?, ?)",
        (task_id, event_type, detail, now),
    )
    conn.commit()
    conn.close()
    print(f"✓ Event logged: {task_id} {event_type}")


# ---------------------------------------------------------------------------
# Import from JSON (legacy workflow)
# ---------------------------------------------------------------------------

def cmd_import_json(json_dir: str, db_path: Optional[Path]):
    """Import tasks from legacy JSON workflow directory.

    支持两种来源：
    1. workflow/task-index.json 中的任务索引
    2. workflow/tasks/*/status.json + steps.json 的 workspace 子目录
    """
    json_path = Path(json_dir).expanduser()
    if not json_path.exists():
        print(f"Directory not found: {json_dir}")
        sys.exit(1)

    task_index = json_path / "task-index.json"
    active_task = json_path / "active-task.json"
    tasks_dir = json_path / "tasks"

    conn = get_db(db_path)
    imported = 0

    def _import_one(tid: str, tdata: dict, sdata: dict, imported_list: list):
        """Import a single task + its steps."""
        now = now_iso()

        # Resolve current step info (steps.json wins, else status.json)
        step_ids = [s["step_id"] for s in sdata.get("steps", [])]
        cur_sid = sdata.get("current_step_id", tdata.get("current_step_id", ""))
        cur_title = sdata.get("current_step_title", "")
        cur_status = sdata.get("current_step_status", "")
        # If current_step_id is a plain step_id (no "step-" prefix), find the step title
        if not cur_title and cur_sid in step_ids:
            for s in sdata.get("steps", []):
                if s["step_id"] == cur_sid:
                    cur_title = s.get("title", "")
                    break
        # Fallback: find the active/rework step
        if not cur_title:
            for s in sdata.get("steps", []):
                if s.get("status") in ("active", "rework"):
                    cur_sid = s["step_id"]
                    cur_title = s.get("title", "")
                    cur_status = s.get("status", "")
                    break

        try:
            conn.execute(
                """INSERT OR IGNORE INTO tasks
                   (task_id, task_title, aliases, original_prompt, task_root,
                    created_at, updated_at, task_status,
                    current_step_id, current_step_title, current_step_status,
                    final_artifact_path, final_export_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tid, tdata.get("task_title", tid),
                 json.dumps(tdata.get("aliases", [])),
                 tdata.get("original_prompt", tdata.get("summary", "")),
                 tdata.get("root", tdata.get("task_root", "")),
                 tdata.get("created_at", now),
                 tdata.get("updated_at", tdata.get("updated_at", now)),
                 tdata.get("status", tdata.get("task_status", "running")),
                 cur_sid, cur_title, cur_status,
                 tdata.get("final_artifact_path", ""),
                 tdata.get("final_export_path", "")),
            )
            for s in sdata.get("steps", []):
                conn.execute(
                    """INSERT OR IGNORE INTO steps
                       (step_id, task_id, step_order, title, goal,
                        allowed_files, acceptance_criteria, constraints,
                        dependencies, status, attempts, owner,
                        started_at, finished_at, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (s.get("step_id", ""), tid,
                     s.get("step_order", 0), s.get("title", ""),
                     s.get("goal", ""),
                     json.dumps(s.get("allowed_files", [])),
                     json.dumps(s.get("acceptance_criteria", [])),
                     json.dumps(s.get("constraints", [])),
                     json.dumps(s.get("dependencies", [])),
                     s.get("status", "pending"),
                     s.get("attempts", 0),
                     s.get("owner", ""),
                     s.get("started_at", ""),
                     s.get("finished_at", ""),
                     now, now),
                )
            imported_list.append(tid)
        except Exception as e:
            print(f"  ! Failed to import {tid}: {e}")

    # Source 1: task-index.json
    if task_index.exists():
        with open(task_index) as f:
            idx = json.load(f)
        tasks_data = idx.get("tasks", {})
        for tid, tdata in tasks_data.items():
            steps_file = json_path / "tasks" / tid / "steps.json"
            sdata = {}
            if steps_file.exists():
                with open(steps_file) as f:
                    sdata = json.load(f)
            _import_one(tid, tdata, sdata, [])
        conn.commit()

    # Source 2: workspace subdirectories (tasks/*/status.json)
    if tasks_dir.exists():
        already_imported = set(
            r[0] for r in conn.execute("SELECT task_id FROM tasks").fetchall()
        )
        for workspace_dir in tasks_dir.iterdir():
            if not workspace_dir.is_dir():
                continue
            tid = workspace_dir.name
            if tid in already_imported:
                continue
            status_file = workspace_dir / "status.json"
            steps_file = workspace_dir / "steps.json"
            if not status_file.exists():
                continue
            with open(status_file) as f:
                tdata = json.load(f)
            sdata = {}
            if steps_file.exists():
                with open(steps_file) as f:
                    sdata = json.load(f)
            _import_one(tid, tdata, sdata, [])
        conn.commit()

    # Import active task
    if active_task.exists():
        with open(active_task) as f:
            at = json.load(f)
        if at.get("active_task_id"):
            conn.execute(
                """INSERT OR REPLACE INTO active_task
                   (id, task_id, task_title, aliases, original_prompt, task_root,
                    current_step_id, current_step_title, task_status, updated_at)
                   VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (at.get("active_task_id"), at.get("active_task_title", ""),
                 json.dumps(at.get("active_task_aliases", [])),
                 at.get("active_task_original_prompt", ""),
                 at.get("active_task_root", ""),
                 at.get("active_step_id", ""),
                 at.get("active_step_title", ""),
                 at.get("active_task_status", ""),
                 at.get("updated_at", now_iso())),
            )
            conn.commit()

    imported = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    print(f"✓ Imported {imported} tasks from {json_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="multi-agent-scheduler SQLite task management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument("--db-path", help="Database path")

    sub = parser.add_subparsers(dest="command", required=True)

    # init
    sub.add_parser("init", help="Initialize database").add_argument("--force", action="store_true")

    # list
    sub.add_parser("list", help="List all tasks")

    # show
    p = sub.add_parser("show", help="Show task details")
    p.add_argument("task_id")

    # current
    sub.add_parser("current", help="Show active task")

    # create
    p = sub.add_parser("create", help="Create a new task")
    p.add_argument("--title", required=True)
    p.add_argument("--root", required=True)
    p.add_argument("--original-prompt", default="")
    p.add_argument("--aliases", nargs="*", default=[])

    # step-add
    p = sub.add_parser("step-add", help="Add a step to a task")
    p.add_argument("task_id")
    p.add_argument("step_title")
    p.add_argument("--goal", default="")
    p.add_argument("--acceptance-criteria", nargs="*", dest="ac", default=[])
    p.add_argument("--allowed-files", nargs="*", dest="allowed", default=[])
    p.add_argument("--constraints", nargs="*", default=[])
    p.add_argument("--dependencies", nargs="*", default=[])
    p.add_argument("--owner", default="")

    # step-set
    p = sub.add_parser("step-set", help="Set step status")
    p.add_argument("step_id")
    p.add_argument("status")

    # step-active
    p = sub.add_parser("step-active", help="Activate a step")
    p.add_argument("step_id")

    # step-done
    p = sub.add_parser("step-done", help="Mark step done")
    p.add_argument("step_id")
    p.add_argument("--decision", required=True)

    # review-add
    p = sub.add_parser("review-add", help="Add a review record")
    p.add_argument("step_id")
    p.add_argument("conclusion", nargs="?", choices=["PASS", "FAIL"])
    p.add_argument("--reason", default="")
    p.add_argument("--issue-count", type=int, default=0)
    p.add_argument("--issue-list", nargs="*", dest="issues", default=[])
    p.add_argument("--fix-mode", default="")
    p.add_argument("--can-proceed", type=int, default=0)
    p.add_argument("--review-notes", default="{}")

    # activate
    p = sub.add_parser("activate", help="Activate a task")
    p.add_argument("task_id")

    # deactivate
    sub.add_parser("deactivate", help="Clear active task")

    # task-set
    p = sub.add_parser("task-set", help="Update task field")
    p.add_argument("task_id")
    p.add_argument("field")
    p.add_argument("value")

    # events
    p = sub.add_parser("events", help="Show task event log")
    p.add_argument("task_id")

    # log
    p = sub.add_parser("log", help="Log a task event")
    p.add_argument("task_id")
    p.add_argument("event_type")
    p.add_argument("detail", nargs="?", default="")

    # import-json
    p = sub.add_parser("import-json", help="Import from legacy JSON")
    p.add_argument("json_dir")

    args = parser.parse_args()
    db = Path(args.db_path) if args.db_path else None

    cmds = {
        "init":          lambda: cmd_init(db, args.force),
        "list":          lambda: cmd_list(db),
        "show":          lambda: cmd_show(args.task_id, db),
        "current":       lambda: cmd_current(db),
        "create":        lambda: cmd_create(args.title, args.root, db, args.original_prompt, args.aliases),
        "activate":      lambda: cmd_activate(args.task_id, db),
        "deactivate":    lambda: cmd_deactivate(db),
        "step-add":      lambda: cmd_step_add(args.task_id, args.step_title, db, args.goal, args.ac, args.allowed, args.constraints, args.dependencies, args.owner),
        "step-set":      lambda: cmd_step_set(args.step_id, args.status, db),
        "step-active":   lambda: cmd_step_active(args.step_id, db),
        "step-done":     lambda: cmd_step_done(args.step_id, args.decision, db),
        "review-add":    lambda: cmd_review_add(args.step_id, args.conclusion, db, args.reason, args.issue_count, args.issues, args.fix_mode, args.can_proceed, json.loads(args.review_notes) if args.review_notes != "{}" else None),
        "task-set":      lambda: cmd_task_set(args.task_id, args.field, args.value, db),
        "events":        lambda: cmd_events(args.task_id, db),
        "log":           lambda: cmd_log(args.task_id, args.event_type, db, args.detail),
        "import-json":   lambda: cmd_import_json(args.json_dir, db),
    }
    cmds[args.command]()


if __name__ == "__main__":
    main()
