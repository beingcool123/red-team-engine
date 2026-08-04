"""Executor node — runs each attack prompt against the target model in parallel."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore[assignment,misc]

from ..state import RedTeamState

load_dotenv()

logger = logging.getLogger(__name__)


def _resolve(run_config: dict[str, str] | None, key: str, env_key: str, default: str = "") -> str:
    """Read from run_config first, then env, then default."""
    if run_config and run_config.get(key):
        return run_config[key]
    return os.getenv(env_key, default)


def get_active_model_name(run_config: dict[str, str] | None = None) -> str:
    return _resolve(run_config, "target_model", "TARGET_MODEL_NAME") or os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")


def get_active_api_key(run_config: dict[str, str] | None = None) -> str:
    return _resolve(run_config, "target_api_key", "TARGET_API_KEY") or os.getenv("GROQ_API_KEY", "")


def get_target_provider(run_config: dict[str, str] | None = None) -> str:
    return _resolve(run_config, "target_provider", "TARGET_PROVIDER", "groq").lower()


def get_target_base_url(run_config: dict[str, str] | None = None) -> str:
    return _resolve(run_config, "target_base_url", "TARGET_BASE_URL", "")


def build_target_llm(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: str | None,
) -> Any:
    """Factory that returns an LLM client for the target (model under test)."""
    provider_name = (provider or "groq").lower()
    if provider_name == "groq":
        return ChatGroq(model=model_name, api_key=api_key, temperature=0.7)
    if provider_name in {"openai", "openai-compatible", "ollama", "local"}:
        if ChatOpenAI is None:
            raise RuntimeError("langchain_openai is not installed. Install it to use OpenAI/Ollama targets.")
        kwargs: dict[str, Any] = {
            "model": model_name,
            "api_key": api_key or "ollama",
            "temperature": 0.7,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)
    raise ValueError(f"Unsupported target provider: {provider_name}")


def is_rate_limit_error(error_text: str) -> bool:
    text = str(error_text).lower()
    return any(
        token in text
        for token in [
            "429",
            "rate limit",
            "too many requests",
            "quota exceeded",
            "temporarily unavailable",
            "timed out",
            "timeout",
        ]
    )


def safe_invoke_with_retry(
    llm: Any,
    prompt_messages: Any,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> str:
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt_messages)
            content = response.content
            if content is None:
                logger.warning("Model returned empty content on attempt %s/%s.", attempt + 1, max_retries)
                return "[ERROR: empty model response]"
            return content.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception as exc:
            error_text = str(exc)
            should_retry = attempt < max_retries - 1
            logger.warning("LLM invoke attempt %s/%s failed: %s", attempt + 1, max_retries, error_text)
            if not should_retry:
                return f"[ERROR after {max_retries} attempts: {error_text}]"

            wait_time = base_delay * (2**attempt)
            if is_rate_limit_error(error_text):
                wait_time *= 3
            logger.info("Retrying LLM invocation in %.2f seconds after failure: %s", wait_time, error_text)
            time.sleep(wait_time)

    return "[ERROR: max retries exceeded]"


def execute_single_attack(
    system_prompt: str,
    user_input: str,
    attack: str,
    run_config: dict[str, str] | None = None,
) -> str:
    model_name = get_active_model_name(run_config)
    api_key = get_active_api_key(run_config)
    provider = get_target_provider(run_config)
    base_url = get_target_base_url(run_config)
    target_llm = build_target_llm(provider, model_name, api_key, base_url)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", f"{user_input}\n\n[ATTACK PROMPT]: {attack}"),
        ]
    )
    return safe_invoke_with_retry(target_llm, prompt.format_messages())


def executor_node(state: RedTeamState) -> RedTeamState:
    """Execute all attack prompts against the target model in parallel threads."""
    prompts: list[str] = state.get("attack_prompts", [])  # type: ignore[assignment]
    run_config = state.get("run_config")
    responses: list[str | None] = [None] * len(prompts)

    if not prompts:
        logger.warning("Executor received an empty attack_prompts list — skipping execution.")
        return {**state, "responses": []}

    max_workers = min(4, max(1, len(prompts)))
    logger.info("Executor launching %d attacks with %d workers.", len(prompts), max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(
                execute_single_attack,
                state["target_system_prompt"],
                state["target_user_input"],
                attack,
                run_config,
            ): idx
            for idx, attack in enumerate(prompts)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            responses[idx] = future.result()

    logger.info("Executor completed %d/%d attacks.", sum(1 for r in responses if r is not None), len(prompts))
    return {**state, "responses": responses}
