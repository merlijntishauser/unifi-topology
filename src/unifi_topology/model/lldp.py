"""LLDP parsing and port label helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .helpers import first_attr
from .ports import extract_port_number, normalize_port_label


@dataclass(frozen=True)
class LLDPEntry:
    chassis_id: str
    port_id: str
    port_desc: str | None = None
    local_port_name: str | None = None
    local_port_idx: int | None = None


def _string_or_none(value: object) -> str | None:
    return str(value) if value else None


def _coerce_local_port_idx(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def coerce_lldp(entry: object) -> LLDPEntry:
    chassis_id = first_attr(entry, "chassis_id", "chassisId")
    port_id = first_attr(entry, "port_id", "portId")
    port_desc = first_attr(entry, "port_desc", "portDesc", "port_descr", "portDescr")
    local_port_name = first_attr(entry, "local_port_name", "localPortName")
    local_port_idx = first_attr(entry, "local_port_idx", "localPortIdx")

    if not chassis_id or not port_id:
        raise ValueError("LLDP entry missing chassis_id or port_id")
    return LLDPEntry(
        chassis_id=str(chassis_id),
        port_id=str(port_id),
        port_desc=_string_or_none(port_desc),
        local_port_name=_string_or_none(local_port_name),
        local_port_idx=_coerce_local_port_idx(local_port_idx),
    )


def _hex_pair(value: str) -> bool:
    return len(value) == 2 and all(ch in "0123456789abcdef" for ch in value)


def _looks_like_mac(value: str | None) -> bool:
    if not value:
        return False
    cleaned = value.strip().lower()
    if cleaned.count(":") == 5:
        return all(_hex_pair(part) for part in cleaned.split(":"))
    return False


def _port_desc_value(entry: LLDPEntry) -> str | None:
    if entry.port_desc and not _looks_like_mac(entry.port_desc):
        return entry.port_desc.strip()
    return None


def _port_name_value(entry: LLDPEntry) -> str | None:
    if entry.local_port_name:
        return normalize_port_label(entry.local_port_name)
    return None


def _port_name_from_port_id(entry: LLDPEntry, name: str | None) -> str | None:
    if entry.port_id and not _looks_like_mac(entry.port_id) and name is None:
        return normalize_port_label(entry.port_id)
    return name


def _resolved_port_number(name: str | None, desc: str | None, number: int | None) -> int | None:
    if number is not None:
        return number
    resolved = extract_port_number(name)
    if resolved is not None:
        return resolved
    return extract_port_number(desc)


def _port_label_parts(entry: LLDPEntry) -> tuple[int | None, str | None, str | None]:
    number = entry.local_port_idx
    name = _port_name_from_port_id(entry, _port_name_value(entry))
    desc = _port_desc_value(entry)
    number = _resolved_port_number(name, desc, number)
    return number, name, desc


def _port_label_from_parts(
    number: int | None,
    name: str | None,
    desc: str | None,
) -> str | None:
    numbered_label = _numbered_port_label(number, desc)
    if numbered_label is not None:
        return numbered_label
    return name or desc


def _numbered_port_label(number: int | None, desc: str | None) -> str | None:
    if number is None:
        return None
    if desc:
        return f"Port {number} ({desc})"
    return f"Port {number}"


def local_port_label(entry: LLDPEntry) -> str | None:
    return _port_label_from_parts(*_port_label_parts(entry))
