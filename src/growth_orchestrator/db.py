"""SQLite persistence. One file, one writer, explicit schema.

SQLite is enough for the prototype (and for the 250 replies/day the scenario implies).
In production this becomes Postgres with the same tables; see README -> Production path.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    country TEXT,
    segment TEXT,
    employee_count INTEGER,
    is_customer INTEGER NOT NULL DEFAULT 0,
    has_open_opportunity INTEGER NOT NULL DEFAULT 0,
    owner_ae_id TEXT,
    csm_id TEXT,
    state_version INTEGER NOT NULL DEFAULT 1,
    state_updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    email TEXT NOT NULL,
    name TEXT,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active',          -- active | waiting | handed_off | suppressed | nurture
    sequence_status TEXT NOT NULL DEFAULT 'none',   -- none | enrolled | paused | completed
    last_outreach_at TEXT,
    wait_until TEXT,
    enriched INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,        -- account | contact | domain
    key TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(scope, key)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,   -- idempotency key supplied by the source system
    type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received',  -- received | processing | processed | ignored_stale | failed
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    processed_at TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS ai_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    mode TEXT NOT NULL,             -- live | offline
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    input_text TEXT NOT NULL,
    raw_output TEXT,
    parsed_json TEXT,
    valid INTEGER NOT NULL DEFAULT 0,
    validation_errors_json TEXT,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    account_id TEXT,
    contact_id TEXT,
    action TEXT NOT NULL,
    automated INTEGER NOT NULL,
    requires_review INTEGER NOT NULL DEFAULT 0,
    reason TEXT NOT NULL,
    trace_json TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    ai_call_id INTEGER,
    policy_version INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
    idempotency_key TEXT PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    event_id TEXT NOT NULL,
    type TEXT NOT NULL,
    target_system TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | in_flight | uncertain | succeeded | failed | dead
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT,
    external_ref TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    event_id TEXT NOT NULL,
    proposed_action TEXT,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',   -- open | approved | rejected
    resolved_by TEXT,
    resolution_note TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    data_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_id);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status, next_attempt_at);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL") if self.path != ":memory:" else None
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)

    # -- low level -----------------------------------------------------------------
    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def reset(self) -> None:
        tables = [
            "audit_log", "review_queue", "actions", "decisions", "ai_calls",
            "events", "suppressions", "contacts", "accounts",
        ]
        with self.tx():
            for t in tables:
                self.conn.execute(f"DELETE FROM {t}")
            self.conn.execute("DELETE FROM sqlite_sequence")

    # -- audit ----------------------------------------------------------------------
    def audit(self, event_id: str | None, stage: str, message: str, data: dict | None = None) -> None:
        self.conn.execute(
            "INSERT INTO audit_log(event_id, stage, message, data_json, created_at) VALUES (?,?,?,?,?)",
            (event_id, stage, message, json.dumps(data, default=str) if data is not None else None, iso(utcnow())),
        )

    def trace(self, event_id: str) -> list[dict[str, Any]]:
        rows = self.all("SELECT * FROM audit_log WHERE event_id = ? ORDER BY id", (event_id,))
        for r in rows:
            r["data"] = json.loads(r.pop("data_json")) if r.get("data_json") else None
        return rows
