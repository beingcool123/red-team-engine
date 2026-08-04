import logging
import os
from dataclasses import asdict, dataclass
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunConfig:
    """Per-run model configuration.  Passed into graph state so nodes
    never need to mutate ``os.environ``."""

    attack_provider: str = "groq"
    attack_model: str = "llama-3.3-70b-versatile"
    attack_api_key: str = ""
    attack_base_url: str = ""
    target_provider: str = "groq"
    target_model: str = "llama-3.3-70b-versatile"
    target_api_key: str = ""
    target_base_url: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)  # type: ignore[return-value]


@dataclass(frozen=True)
class Settings:
    model_name: str
    groq_api_key: str
    owasp_enabled: bool
    max_retries: int = 5
    max_workers: int = 4
    timeout_seconds: int = 60

    def as_dict(self) -> dict[str, Any]:
        return {
            "MODEL_NAME": self.model_name,
            "GROQ_API_KEY": "***REDACTED***",
            "OWASP_ENABLED": self.owasp_enabled,
            "MAX_RETRIES": self.max_retries,
            "MAX_WORKERS": self.max_workers,
            "TIMEOUT_SECONDS": self.timeout_seconds,
        }


def get_settings() -> Settings:
    model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    owasp_enabled = os.getenv("OWASP_ENABLED", "true").lower() == "true"
    max_retries = int(os.getenv("MAX_RETRIES", "5"))
    max_workers = int(os.getenv("MAX_WORKERS", "4"))
    timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "60"))

    settings = Settings(
        model_name=str(model_name).strip(),
        groq_api_key=str(groq_api_key).strip(),
        owasp_enabled=owasp_enabled,
        max_retries=max_retries,
        max_workers=max_workers,
        timeout_seconds=timeout_seconds,
    )

    errors: list[str] = []
    if not settings.model_name:
        errors.append("MODEL_NAME is empty.")
    if not settings.groq_api_key:
        errors.append("GROQ_API_KEY is missing. Set it in your .env file or environment.")
    if settings.max_retries < 1:
        errors.append("MAX_RETRIES must be at least 1.")
    if settings.max_workers < 1:
        errors.append("MAX_WORKERS must be at least 1.")
    if settings.timeout_seconds < 1:
        errors.append("TIMEOUT_SECONDS must be at least 1.")

    if errors:
        logger.error("Runtime configuration validation failed: %s", "; ".join(errors))
        raise ValueError("; ".join(errors))

    logger.info("Runtime configuration validated successfully.")
    return settings


def validate_runtime_config() -> dict[str, Any]:
    """Compatibility wrapper for existing app startup validation."""
    return get_settings().as_dict()


# ---------------------------------------------------------------------------
# Module-level constants kept for backward compatibility with any direct imports
# ---------------------------------------------------------------------------
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
OWASP_ENABLED: bool = os.getenv("OWASP_ENABLED", "true").lower() == "true"
