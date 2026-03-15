"""Private helpers for edge and port label formatting."""

from __future__ import annotations

from dataclasses import dataclass


def _extract_port_text(side: str) -> str | None:
    candidate = side.split(":", 1)[1].strip() if ":" in side else side.strip()
    if candidate.lower().startswith("port "):
        return candidate
    return None


def _extract_device_name(side: str) -> str | None:
    if ":" not in side:
        return None
    name = side.split(":", 1)[0].strip()
    return name or None


def _format_compact_ports(
    left_name: str | None,
    left_port: str | None,
    right_port: str | None,
    label: str,
) -> str:
    if left_port and right_port:
        if left_name:
            return f"{left_name} {left_port} <-> {right_port}"
        return f"{left_port} <-> {right_port}"
    return left_port or right_port or label


@dataclass(frozen=True)
class _EdgeLabelSide:
    device_name: str | None
    port_text: str | None


def _edge_label_side(segment: str) -> _EdgeLabelSide:
    return _EdgeLabelSide(
        device_name=_extract_device_name(segment),
        port_text=_extract_port_text(segment),
    )


def _ordered_edge_label_sides(
    left_side: _EdgeLabelSide,
    right_side: _EdgeLabelSide,
    *,
    left_node: str | None,
    right_node: str | None,
) -> tuple[_EdgeLabelSide, _EdgeLabelSide]:
    if not left_node or not right_node:
        return left_side, right_side
    if right_side.device_name == left_node and left_side.device_name == right_node:
        return right_side, left_side
    return left_side, right_side


def _compact_edge_label(
    label: str, *, left_node: str | None = None, right_node: str | None = None
) -> str:
    if "<->" not in label:
        return label
    left_segment, right_segment = (part.strip() for part in label.split("<->", 1))
    left_side, right_side = _ordered_edge_label_sides(
        _edge_label_side(left_segment),
        _edge_label_side(right_segment),
        left_node=left_node,
        right_node=right_node,
    )
    return _format_compact_ports(
        left_side.device_name,
        left_side.port_text,
        right_side.port_text,
        label,
    )


def _port_only(segment: str) -> str:
    port = _extract_port_text(segment)
    if port:
        return port
    lower = segment.lower()
    idx = lower.rfind("port ")
    if idx != -1:
        return segment[idx:].strip()
    return segment.split(":", 1)[-1].strip()


def _truncate_port_text(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _bidirectional_port_label_lines(
    port_label: str,
    *,
    prefix: str,
    max_chars: int,
) -> list[str]:
    left_part, right_part = (part.strip() for part in port_label.split("<->", 1))
    front_text = _truncate_port_text(f"{prefix}: {_port_only(left_part)}", max_chars=max_chars)
    side_text = _truncate_port_text(f"local: {_port_only(right_part)}", max_chars=max_chars)
    return [line for line in (front_text, side_text) if line]


def _single_port_label_lines(
    port_label: str,
    *,
    prefix: str,
    max_chars: int,
) -> list[str]:
    side_text = _truncate_port_text(f"{prefix}: {_port_only(port_label)}", max_chars=max_chars)
    return [side_text]


def _format_port_label_lines(
    port_label: str,
    *,
    prefix: str,
    max_chars: int,
) -> list[str]:
    if "<->" in port_label:
        return _bidirectional_port_label_lines(port_label, prefix=prefix, max_chars=max_chars)
    return _single_port_label_lines(port_label, prefix=prefix, max_chars=max_chars)
