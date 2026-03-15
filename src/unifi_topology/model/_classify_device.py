"""Private device classification helpers."""

from __future__ import annotations

from .helpers import get_field

_GATEWAY_TYPES = frozenset({"gateway", "ugw", "usg", "udm", "udr", "uxg"})
_SWITCH_TYPES = frozenset({"switch", "usw"})
_AP_TYPES = frozenset({"uap", "ap"})


def _classify_by_device_name(name: str) -> str | None:
    """Classify device by name when type field is missing."""
    lower = name.strip().lower()
    if "gateway" in lower or lower.startswith("gw"):
        return "gateway"
    if "switch" in lower:
        return "switch"
    if "ap" in lower:
        return "ap"
    return None


def _normalized_device_type(device: object) -> str:
    raw_type = get_field(device, "type")
    return raw_type.strip().lower() if isinstance(raw_type, str) else ""


def _classify_known_device_type(value: str, *, in_gateway_mode: object) -> str | None:
    if value in _GATEWAY_TYPES:
        return "gateway"
    if value == "ux":
        return "ap" if in_gateway_mode is False else "gateway"
    if value in _SWITCH_TYPES:
        return "switch"
    if value in _AP_TYPES or "ap" in value:
        return "ap"
    return None


def classify_device_type(device: object) -> str:
    """Classify a network device into gateway, switch, ap, or other."""
    value = _normalized_device_type(device)
    if not value:
        raw_name = get_field(device, "name")
        name = raw_name if isinstance(raw_name, str) else ""
        return _classify_by_device_name(name) or "other"
    return _classify_known_device_type(value, in_gateway_mode=get_field(device, "in_gateway_mode")) or "other"
