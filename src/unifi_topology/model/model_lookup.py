"""Look up friendly product names for UniFi model codes.

Uses the bundled ``assets/models.json`` file (scraped from the official
Ubiquiti store) to resolve short model codes to human-readable names.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODELS_PATH = Path(__file__).resolve().parent.parent / "assets" / "models.json"
_cache: dict[str, dict[str, str]] | None = None


def _load_models() -> dict[str, dict[str, str]]:
    """Load the model lookup table (cached after first call)."""
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache
    try:
        data: dict[str, Any] = json.loads(_MODELS_PATH.read_text())
        _cache = data.get("models", {})
    except (OSError, json.JSONDecodeError):
        logger.debug("Could not load model lookup table from %s", _MODELS_PATH)
        _cache = {}
    return _cache or {}


def lookup_model_name(model: str) -> str:
    """Return the friendly product name for a UniFi model code.

    Falls back to case-insensitive matching.  Returns an empty string
    if no match is found.
    """
    models = _load_models()
    entry = models.get(model)
    if entry is not None:
        return entry["name"]
    lower = model.lower()
    for key, value in models.items():
        if key.lower() == lower:
            return value["name"]
    return ""


def lookup_model_url(model: str) -> str:
    """Return the store product URL for a UniFi model code.

    Returns an empty string if no match is found.
    """
    models = _load_models()
    entry = models.get(model)
    if entry is not None:
        return entry.get("url", "")
    lower = model.lower()
    for key, value in models.items():
        if key.lower() == lower:
            return value.get("url", "")
    return ""
