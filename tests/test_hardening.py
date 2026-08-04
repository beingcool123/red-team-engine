"""Original hardening tests — updated to work with the refactored RunConfig API."""

from __future__ import annotations

from typing import Any

from app import build_run_summary, compare_run_history, format_score, get_score_status
from graph.nodes.executor import build_target_llm
from graph.nodes.judge import normalize_score_value
from graph.nodes.planner import get_attack_model_name


def test_normalize_score_value_accepts_valid_numeric_value() -> None:
    score, reason = normalize_score_value(8)
    assert score == 8
    assert reason is None

    score, reason = normalize_score_value("7")
    assert score == 7
    assert reason is None


def test_normalize_score_value_rejects_invalid_values() -> None:
    score, reason = normalize_score_value("JUDGE_ERROR")
    assert score is None
    assert reason == "invalid_score"

    score, reason = normalize_score_value("abc")
    assert score is None
    assert reason == "invalid_score"


def test_score_status_handles_review_states() -> None:
    assert get_score_status("JUDGE_ERROR") == "⚠️ Review Required"
    assert get_score_status(8) == "🟢 Safe"
    assert format_score("JUDGE_ERROR") == "JUDGE_ERROR"


def test_build_run_summary_counts_valid_and_review_scores() -> None:
    summary = build_run_summary(
        {
            "target_system_prompt": "System prompt",
            "target_user_input": "User input",
            "scores": [8, "JUDGE_ERROR", 2, "API_ERROR"],
            "vulnerabilities": [{"score": 2}, {"score": "JUDGE_ERROR"}],
            "attack_categories": ["JAILBREAK", "PHISHING", "PROMPT_INJECTION", "MISINFORMATION"],
        }
    )
    assert summary["pass_count"] == 1
    assert summary["error_count"] == 2
    assert summary["vulnerability_count"] == 1
    assert summary["total_checks"] == 4


def test_compare_run_history_returns_delta_metrics() -> None:
    left: dict[str, Any] = {"summary": {"pass_count": 4, "vulnerability_count": 1, "error_count": 0, "review_count": 0}}
    right: dict[str, Any] = {"summary": {"pass_count": 2, "vulnerability_count": 3, "error_count": 1, "review_count": 1}}
    comparison = compare_run_history(left, right)
    assert comparison["pass_delta"] == -2
    assert comparison["vulnerability_delta"] == 2
    assert comparison["error_delta"] == 1


def test_build_target_llm_returns_groq_client_for_groq_provider() -> None:
    llm = build_target_llm("groq", "llama-3.3-70b-versatile", "demo-key", None)
    assert llm.__class__.__name__ == "ChatGroq"


def test_build_target_llm_returns_openai_client_for_ollama_provider() -> None:
    llm = build_target_llm("ollama", "llama3.1:8b", "ollama", "http://localhost:11434/v1")
    assert llm.__class__.__name__ == "ChatOpenAI"
    assert llm.openai_api_base == "http://localhost:11434/v1"


def test_attack_model_uses_run_config_over_env(monkeypatch: Any) -> None:
    """get_attack_model_name should prefer run_config over os.environ."""
    monkeypatch.setenv("MODEL_NAME", "env-model")
    monkeypatch.setenv("ATTACK_MODEL_NAME", "env-attack-model")

    # Without run_config: falls back to env
    assert get_attack_model_name() == "env-attack-model"

    # With run_config: prefers run_config
    run_config = {"attack_model": "config-attack-model"}
    assert get_attack_model_name(run_config) == "config-attack-model"  # type: ignore[arg-type]


def test_attack_model_env_fallback_for_legacy_callers(monkeypatch: Any) -> None:
    """Backward compat: nodes still work if no run_config is passed."""
    monkeypatch.setenv("ATTACK_MODEL_NAME", "legacy-model")
    assert get_attack_model_name(None) == "legacy-model"
