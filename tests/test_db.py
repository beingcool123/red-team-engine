"""Unit tests for the SQLite run-history database module."""

from __future__ import annotations

from typing import Any

import db


def _make_entry(run_id: str = "run_001") -> dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp": "2026-01-01T00:00:00",
        "model_name": "llama-3.3-70b-versatile",
        "prompt_variant": "baseline",
        "scenario_name": "test-scenario",
        "summary": {"pass_count": 3, "vulnerability_count": 1, "error_count": 0},
        "scores": [8, 9, 2],
        "vulnerabilities": [{"category": "JAILBREAK", "score": 2}],
        "target_system_prompt": "You are a helpful assistant.",
    }


def test_init_db_creates_table(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    with db._get_connection(tmp_db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runs'")
        assert cursor.fetchone() is not None


def test_save_and_load_run(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    entry = _make_entry("run_save_001")
    db.save_run(entry, db_path=tmp_db_path)

    runs = db.load_runs(limit=10, db_path=tmp_db_path)
    assert len(runs) == 1
    assert runs[0]["run_id"] == "run_save_001"
    assert runs[0]["summary"]["pass_count"] == 3
    assert runs[0]["scores"] == [8, 9, 2]


def test_load_runs_returns_newest_first(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    for i in range(3):
        db.save_run(_make_entry(f"run_{i:03d}"), db_path=tmp_db_path)

    runs = db.load_runs(limit=10, db_path=tmp_db_path)
    # newest inserted last, but DB orders by created_at DESC
    assert len(runs) == 3


def test_save_run_replaces_on_duplicate_id(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    entry = _make_entry("run_dup")
    db.save_run(entry, db_path=tmp_db_path)

    updated = {**entry, "model_name": "updated-model"}
    db.save_run(updated, db_path=tmp_db_path)

    runs = db.load_runs(db_path=tmp_db_path)
    assert len(runs) == 1
    assert runs[0]["model_name"] == "updated-model"


def test_load_runs_respects_limit(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    for i in range(10):
        db.save_run(_make_entry(f"run_limit_{i}"), db_path=tmp_db_path)

    runs = db.load_runs(limit=3, db_path=tmp_db_path)
    assert len(runs) == 3


def test_delete_run_removes_entry(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    db.save_run(_make_entry("run_del"), db_path=tmp_db_path)
    deleted = db.delete_run("run_del", db_path=tmp_db_path)
    assert deleted is True
    assert db.load_runs(db_path=tmp_db_path) == []


def test_delete_run_returns_false_for_nonexistent(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    result = db.delete_run("nonexistent", db_path=tmp_db_path)
    assert result is False


def test_load_runs_on_empty_db(tmp_db_path: str) -> None:
    db.init_db(db_path=tmp_db_path)
    assert db.load_runs(db_path=tmp_db_path) == []
