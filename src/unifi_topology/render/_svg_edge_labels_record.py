"""Private helpers for recording edge labels onto rendered nodes."""

from __future__ import annotations

from dataclasses import dataclass

from ..model.topology import Edge
from .svg_labels import (
    _compact_edge_label,
    _extract_device_name,
    _extract_port_text,
    _strip_local_port,
)


@dataclass(frozen=True)
class EdgeLabelContext:
    compact_label: str
    upstream_part: str


def _edge_label_context(edge: Edge) -> EdgeLabelContext | None:
    raw_label = edge.label
    if not raw_label:
        return None
    return EdgeLabelContext(
        compact_label=_compact_edge_label(raw_label, left_node=edge.left, right_node=edge.right),
        upstream_part=raw_label.split("<->", 1)[0].strip(),
    )


def _client_attachment(
    edge: Edge,
    node_types: dict[str, str],
) -> tuple[str, str] | None:
    left_type = node_types.get(edge.left, "other")
    right_type = node_types.get(edge.right, "other")
    if left_type == "client" and right_type != "client":
        return edge.left, edge.right
    if right_type == "client" and left_type != "client":
        return edge.right, edge.left
    return None


def _upstream_name_from_label(context: EdgeLabelContext) -> str | None:
    return _extract_device_name(context.upstream_part)


def _client_port_text(context: EdgeLabelContext) -> str:
    return _extract_port_text(context.upstream_part) or context.compact_label


def _infra_label_text(
    context: EdgeLabelContext,
    right_type: str,
    *,
    upstream_name: str,
) -> str:
    label_text = context.compact_label
    if label_text.lower().startswith("port "):
        label_text = f"{upstream_name} {label_text}"
    return _strip_local_port(label_text, right_type)
