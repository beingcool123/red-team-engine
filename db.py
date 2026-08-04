"""Persistent run history backed by SQLite.

Usage:
    import db
    db.init_db()
    db.save_run(entry)
    runs = db.load_runs(limit=20)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("RUN_HISTORY_DB", os.path.join("reports", "run_history.db"))


def _get_connection(db_path: str = _DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = _DB_PATH) -> None:
    """Create the runs table if it does not already exist."""
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL UNIQUE,
                timestamp   TEXT    NOT NULL,
                model_name  TEXT,
                prompt_variant TEXT,
                scenario_name  TEXT,
                summary     TEXT,
                scores      TEXT,
                vulnerabilities TEXT,
                target_system_prompt TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    logger.info("Database initialised at %s.", db_path)


def save_run(entry: dict[str, Any], db_path: str = _DB_PATH) -> None:
    """Persist a single run entry dict to the database."""
    try:
        with _get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs
                    (run_id, timestamp, model_name, prompt_variant, scenario_name,
                     summary, scores, vulnerabilities, target_system_prompt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.get("run_id", ""),
                    entry.get("timestamp", ""),
                    entry.get("model_name", ""),
                    entry.get("prompt_variant", ""),
                    entry.get("scenario_name", ""),
                    json.dumps(entry.get("summary", {})),
                    json.dumps(entry.get("scores", [])),
                    json.dumps(entry.get("vulnerabilities", [])),
                    entry.get("target_system_prompt", ""),
                ),
            )
            conn.commit()
        logger.info("Run %s persisted to database.", entry.get("run_id"))
    except sqlite3.Error as exc:
        logger.error("Failed to save run %s to database: %s", entry.get("run_id"), exc)


def load_runs(limit: int = 20, db_path: str = _DB_PATH) -> list[dict[str, Any]]:
    """Load the most recent *limit* runs from the database, newest first."""
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT run_id, timestamp, model_name, prompt_variant, scenario_name,
                       summary, scores, vulnerabilities, target_system_prompt
                FROM runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "run_id": row["run_id"],
                    "timestamp": row["timestamp"],
                    "model_name": row["model_name"],
                    "prompt_variant": row["prompt_variant"],
                    "scenario_name": row["scenario_name"],
                    "summary": json.loads(row["summary"] or "{}"),
                    "scores": json.loads(row["scores"] or "[]"),
                    "vulnerabilities": json.loads(row["vulnerabilities"] or "[]"),
                    "target_system_prompt": row["target_system_prompt"],
                }
            )
        return result
    except sqlite3.Error as exc:
        logger.error("Failed to load runs from database: %s", exc)
        return []


def delete_run(run_id: str, db_path: str = _DB_PATH) -> bool:
    """Delete a single run by run_id. Returns True if a row was deleted."""
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Run %s deleted from database.", run_id)
        return deleted
    except sqlite3.Error as exc:
        logger.error("Failed to delete run %s: %s", run_id, exc)
        return False
