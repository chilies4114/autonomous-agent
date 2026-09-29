from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """SQLite-backed durable queue, observations, errors, and audit decisions."""

    def __init__(self, state_path: str | Path):
        self.path = Path(state_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, url TEXT, goal TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued', retries INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, url TEXT NOT NULL,
                    title TEXT, summary TEXT, content_hash TEXT NOT NULL, fetched_at TEXT NOT NULL,
                    UNIQUE(url, content_hash)
                );
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, url TEXT,
                    error TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, decision TEXT NOT NULL,
                    details TEXT, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_errors_task ON errors(task_id);
                """
            )

    def enqueue(self, item: Dict[str, Any]) -> bool:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        task_id = item.get("id") or hashlib.sha256(item["goal"].encode()).hexdigest()[:16]
        with self._connect() as db:
            cursor = db.execute(
                """INSERT OR IGNORE INTO tasks
                   (id, url, goal, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'queued', ?, ?)""",
                (task_id, item.get("url"), item["goal"], now, now),
            )
        return cursor.rowcount == 1

    def queued_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM tasks WHERE status='queued' ORDER BY created_at LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_done(self, task_id: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE tasks SET status='done', updated_at=datetime('now') WHERE id=?", (task_id,))

    def mark_retry(self, task_id: str, error: str) -> None:
        with self._connect() as db:
            db.execute(
                """UPDATE tasks SET retries=retries+1, last_error=?, updated_at=datetime('now')
                   WHERE id=?""", (error, task_id)
            )

    def discard(self, task_id: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE tasks SET status='discarded', updated_at=datetime('now') WHERE id=?", (task_id,))

    def add_observation(self, observation: Dict[str, Any]) -> None:
        content_hash = hashlib.sha256(observation.get("text", observation.get("summary", "")).encode()).hexdigest()
        with self._connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO observations
                   (task_id, url, title, summary, content_hash, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (observation.get("task_id"), observation["url"], observation.get("title", ""),
                 observation.get("summary", ""), content_hash, observation["timestamp"]),
            )

    def add_error(self, error: Dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO errors (task_id, url, error, created_at) VALUES (?, ?, ?, ?)",
                (error.get("task_id"), error.get("url"), error["error"], error["timestamp"]),
            )

    def add_decision(self, decision: Dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO decisions (task_id, decision, details, created_at) VALUES (?, ?, ?, ?)",
                (decision.get("task_id"), decision["decision"], json.dumps(decision.get("details", {})), decision["timestamp"]),
            )

    def last_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM errors ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> Dict[str, int]:
        with self._connect() as db:
            rows = db.execute("SELECT status, COUNT(*) AS count FROM tasks GROUP BY status").fetchall()
        return {row["status"]: row["count"] for row in rows}
