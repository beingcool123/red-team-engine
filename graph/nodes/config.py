"""Backward-compat shim — import from the top-level config module instead."""

from config import GROQ_API_KEY, MODEL_NAME, OWASP_ENABLED

__all__ = ["GROQ_API_KEY", "MODEL_NAME", "OWASP_ENABLED"]
