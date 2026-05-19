#!/usr/bin/env python3
"""
init_db.py — 初始化 multi-agent-scheduler SQLite 数据库

用法:
  python3 init_db.py [--db-path PATH] [--force] [--verify]

选项:
  --db-path PATH   指定数据库路径 (默认: ~/.hermes/multi-agent-scheduler.db)
  --force          如果已存在数据库则重新初始化（会丢失数据）
  --verify         仅验证数据库完整性，不重建
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from db_schema import SCHEMA_SQL


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def resolve_db_path(path: Optional[str]) -> Path:
    if path:
        return Path(path).expanduser()
    return Path.home() / ".hermes" / "multi-agent-scheduler.db"


def init_db(db_path: Path, force: bool = False) -> None:
    """Initialize the database with the full schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    file_existed = db_path.exists()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    if file_existed and force:
        print(f"Reinitializing database at {db_path} ...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for (table_name,) in cursor.fetchall():
            if table_name != "sqlite_sequence":
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    elif file_existed and not force:
        print(f"Database already exists at {db_path}")
        print("Use --force to reinitialize (will lose data).")
        conn.close()
        return

    # Apply full schema via executescript
    cursor.executescript(SCHEMA_SQL)

    # Insert schema version record
    cursor.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (1, now_iso()),
    )

    conn.commit()
    conn.close()
    print(f"Database initialized: {db_path}")


def verify_db(db_path: Path) -> bool:
    """Verify database integrity: check schema_version table exists and list tables."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check schema_version exists
        cursor.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        )
        row = cursor.fetchone()
        version = row[0] if row else "unknown"

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]

        conn.close()

        print(f"Database OK: {db_path}")
        print(f"  Schema version: {version}")
        print(f"  Tables: {tables}")
        return True
    except sqlite3.OperationalError as e:
        print(f"Database corrupted or incomplete: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize multi-agent-scheduler SQLite database"
    )
    parser.add_argument(
        "--db-path",
        help="Database path (default: ~/.hermes/multi-agent-scheduler.db)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Reinitialize if exists"
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify DB only, don't modify"
    )
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)

    if args.verify:
        success = verify_db(db_path)
        sys.exit(0 if success else 1)
    else:
        init_db(db_path, force=args.force)
        sys.exit(0)


if __name__ == "__main__":
    main()
