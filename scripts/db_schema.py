"""
SQLite schema definition for multi-agent-scheduler.

Tables:
  - tasks:        主任务表
  - steps:       步骤表（外键 -> tasks.task_id）
  - reviews:     审查记录表（外键 -> steps）
  - active_task: 当前激活任务（单行）
  - event_log:   事件审计日志
  - schema_version: schema 版本记录

索引策略：
  - tasks: task_id(PK), task_title, task_status
  - steps: step_id(PK), task_id(FK), step_status, step_order
  - reviews: review_id(PK), step_id(FK), review_time DESC
"""

SCHEMA_SQL = """
-- 主任务表
CREATE TABLE IF NOT EXISTS tasks (
    task_id              TEXT    PRIMARY KEY,
    task_title           TEXT    NOT NULL,
    aliases              TEXT    NOT NULL DEFAULT '[]',
    original_prompt      TEXT    NOT NULL DEFAULT '',
    task_root            TEXT    NOT NULL,
    role_map_version     TEXT    NOT NULL DEFAULT '',
    log_version          TEXT    NOT NULL DEFAULT 'v3',
    created_at           TEXT    NOT NULL,
    updated_at           TEXT    NOT NULL,
    task_status          TEXT    NOT NULL DEFAULT 'running',
    current_step_id      TEXT    NOT NULL DEFAULT '',
    current_step_title   TEXT    NOT NULL DEFAULT '',
    current_step_status  TEXT    NOT NULL DEFAULT '',
    final_artifact_path  TEXT    NOT NULL DEFAULT '',
    final_export_path    TEXT    NOT NULL DEFAULT '',
    ready_for_user_confirm INTEGER NOT NULL DEFAULT 0
);

-- 步骤表
CREATE TABLE IF NOT EXISTS steps (
    step_id              TEXT    PRIMARY KEY,
    task_id              TEXT    NOT NULL,
    step_order           INTEGER NOT NULL DEFAULT 0,
    title                TEXT    NOT NULL,
    goal                 TEXT    NOT NULL DEFAULT '',
    allowed_files        TEXT    NOT NULL DEFAULT '[]',
    acceptance_criteria  TEXT    NOT NULL DEFAULT '[]',
    constraints          TEXT    NOT NULL DEFAULT '[]',
    dependencies         TEXT    NOT NULL DEFAULT '[]',
    status               TEXT    NOT NULL DEFAULT 'pending',
    attempts             INTEGER NOT NULL DEFAULT 0,
    owner                TEXT    NOT NULL DEFAULT '',
    started_at           TEXT    NOT NULL DEFAULT '',
    finished_at          TEXT    NOT NULL DEFAULT '',
    implementation_summary TEXT  NOT NULL DEFAULT '',
    review_summary       TEXT    NOT NULL DEFAULT '',
    decision             TEXT    NOT NULL DEFAULT '',
    known_risks          TEXT    NOT NULL DEFAULT '[]',
    related_files        TEXT    NOT NULL DEFAULT '[]',
    created_at           TEXT    NOT NULL,
    updated_at           TEXT    NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 审查记录表
CREATE TABLE IF NOT EXISTS reviews (
    review_id            TEXT    PRIMARY KEY,
    step_id              TEXT    NOT NULL,
    task_id              TEXT    NOT NULL,
    reviewer             TEXT    NOT NULL,
    review_time          TEXT    NOT NULL,
    review_basis         TEXT    NOT NULL DEFAULT '{}',
    dev_submission       TEXT    NOT NULL DEFAULT '{}',
    checks_performed     TEXT    NOT NULL DEFAULT '{}',
    conclusion           TEXT    NOT NULL,
    reason               TEXT    NOT NULL DEFAULT '',
    fix_mode             TEXT    NOT NULL DEFAULT '',
    can_proceed          INTEGER NOT NULL DEFAULT 0,
    issue_count          INTEGER NOT NULL DEFAULT 0,
    issue_list           TEXT    NOT NULL DEFAULT '[]',
    review_notes         TEXT    NOT NULL DEFAULT '{}',
    review_ref           TEXT    NOT NULL DEFAULT '',
    created_at           TEXT    NOT NULL,
    FOREIGN KEY (step_id) REFERENCES steps(step_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 当前激活任务（单行表）
CREATE TABLE IF NOT EXISTS active_task (
    id                   INTEGER PRIMARY KEY CHECK (id = 1),
    task_id              TEXT    NOT NULL DEFAULT '',
    task_title           TEXT    NOT NULL DEFAULT '',
    aliases              TEXT    NOT NULL DEFAULT '[]',
    original_prompt      TEXT    NOT NULL DEFAULT '',
    task_root            TEXT    NOT NULL DEFAULT '',
    current_step_id      TEXT    NOT NULL DEFAULT '',
    current_step_title   TEXT    NOT NULL DEFAULT '',
    task_status          TEXT    NOT NULL DEFAULT '',
    updated_at           TEXT    NOT NULL
);

-- 事件日志表（审计轨迹）
CREATE TABLE IF NOT EXISTS event_log (
    event_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id              TEXT    NOT NULL,
    step_id              TEXT    NOT NULL DEFAULT '',
    event_type           TEXT    NOT NULL,
    actor                TEXT    NOT NULL,
    detail               TEXT    NOT NULL DEFAULT '',
    created_at           TEXT    NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- Schema 版本记录
CREATE TABLE IF NOT EXISTS schema_version (
    version              INTEGER PRIMARY KEY,
    applied_at           TEXT    NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_steps_task_id     ON steps(task_id);
CREATE INDEX IF NOT EXISTS idx_steps_status      ON steps(status);
CREATE INDEX IF NOT EXISTS idx_reviews_step_id   ON reviews(step_id);
CREATE INDEX IF NOT EXISTS idx_reviews_task_id   ON reviews(task_id);
CREATE INDEX IF NOT EXISTS idx_event_log_task_id ON event_log(task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status      ON tasks(task_status);
CREATE INDEX IF NOT EXISTS idx_tasks_title       ON tasks(task_title);
"""
