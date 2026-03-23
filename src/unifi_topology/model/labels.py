"""Edge label helpers."""

from __future__ import annotations

from collections.abc import Callable


def _resolve_display_names(
    left: str,
    right: str,
    node_names: dict[str, str] | None,
) -> tuple[str, str]:
    names = node_names or {}
    return names.get(left, left), names.get(right, right)


def compose_port_label(
    left: str,
    right: str,
    port_map: dict[tuple[str, str], str],
    node_names: dict[str, str] | None = None,
) -> str | None:
    left_name, right_name = _resolve_display_names(left, right, node_names)
    left_label = port_map.get((left, right))
    right_label = port_map.get((right, left))
    if left_label and right_label:
        return f"{left_name}: {left_label} <-> {right_name}: {right_label}"
    if left_label:
        return f"{left_name}: {left_label} <-> {right_name}: ?"
    if right_label:
        return f"{left_name}: ? <-> {right_name}: {right_label}"
    return None


def _should_reverse_by_labels(
    left_label: str | None,
    right_label: str | None,
) -> bool:
    return left_label is None and right_label is not None


def _should_reverse_by_rank(
    left: str,
    right: str,
    *,
    left_label: str | None,
    right_label: str | None,
    rank_for_name: Callable[[str], int],
) -> bool:
    if not (left_label and right_label):
        return False
    left_rank = rank_for_name(left)
    right_rank = rank_for_name(right)
    return (left_rank, left.lower()) > (right_rank, right.lower())


def order_edge_names(
    left: str,
    right: str,
    port_map: dict[tuple[str, str], str],
    rank_for_name: Callable[[str], int],
) -> tuple[str, str]:
    left_label = port_map.get((left, right))
    right_label = port_map.get((right, left))
    if _should_reverse_by_labels(left_label, right_label):
        return (right, left)
    if _should_reverse_by_rank(
        left,
        right,
        left_label=left_label,
        right_label=right_label,
        rank_for_name=rank_for_name,
    ):
        return (right, left)
    return (left, right)
