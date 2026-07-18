"""Shared low-level helpers for the model layer.

These tiny pure functions are used across multiple model modules.
Centralising them here avoids circular-import issues and duplication.
"""

from __future__ import annotations

from collections.abc import Iterable


def _iterable_list(value: object) -> list[object] | None:
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        return list(value)
    return None


def as_list(value: object | None) -> list[object]:
    """Coerce *value* to a list, handling dicts, iterables, and None."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return _iterable_list(value) or []


def as_bool(value: object | None) -> bool:
    """Coerce *value* to a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def as_int(value: object | None, default: int = 0) -> int:
    """Coerce *value* to an integer."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return _parse_int_string(value, default)
    return default


def _parse_int_string(value: str, default: int) -> int:
    try:
        return int(value.strip())
    except ValueError:
        return default


def first_attr(obj: object, *names: str) -> object | None:
    """Return the first non-None field value from *names*."""
    for name in names:
        value = get_field(obj, name)
        if value is not None:
            return value
    return None


def first_string_field(obj: object, *keys: str) -> str | None:
    """Return the first non-empty stripped string from *keys*."""
    for key in keys:
        value = get_field(obj, key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_mac(value: str) -> str:
    """Normalize a MAC to lowercase colon-separated form.

    Strings that are not 12 hex digits (e.g. a third-party device name used as
    an LLDP chassis id) are only stripped and lowercased, not reformatted.
    """
    stripped = value.strip().lower()
    hex_digits = stripped.replace(":", "").replace("-", "").replace(".", "")
    if len(hex_digits) == 12 and all(c in "0123456789abcdef" for c in hex_digits):
        return ":".join(hex_digits[i : i + 2] for i in range(0, 12, 2))
    return stripped


def get_field(obj: object, name: str) -> object | None:
    """Read a named field from a dict **or** an attribute-style object."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
