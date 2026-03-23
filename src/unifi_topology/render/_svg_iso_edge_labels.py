"""Private helpers for isometric edge label recording."""

from __future__ import annotations

from ..model.topology import Edge
from . import _svg_edge_labels_record
from .svg_labels import _shorten_prefix

__all__ = [
    "_client_attachment",
    "_client_port_text",
    "_edge_label_context",
    "_infra_label_text",
    "_iso_client_attachment",
    "_record_iso_client_edge_label",
    "_record_iso_device_edge_label",
    "_record_iso_edge_label",
    "_record_iso_edge_labels",
    "_upstream_name_from_label",
]

_client_attachment = _svg_edge_labels_record._client_attachment
_client_port_text = _svg_edge_labels_record._client_port_text
_edge_label_context = _svg_edge_labels_record._edge_label_context
_infra_label_text = _svg_edge_labels_record._infra_label_text
_upstream_name_from_label = _svg_edge_labels_record._upstream_name_from_label


def _record_iso_edge_labels(
    edges: list[Edge],
    node_types: dict[str, str],
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
    node_names: dict[str, str] | None = None,
) -> None:
    for edge in edges:
        _record_iso_edge_label(edge, node_types, node_port_labels, node_port_prefix, node_names)


def _record_iso_edge_label(
    edge: Edge,
    node_types: dict[str, str],
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
    node_names: dict[str, str] | None = None,
) -> None:
    context = _edge_label_context(edge, node_names=node_names)
    if context is None:
        return
    client_attachment = _client_attachment(edge, node_types)
    if client_attachment is not None:
        client_node, upstream_node = client_attachment
        upstream_display = context.right_name if upstream_node == edge.right else context.left_name
        _record_iso_client_edge_label(
            context,
            client_node,
            upstream_display,
            node_port_labels,
            node_port_prefix,
        )
        return
    _record_iso_device_edge_label(
        edge,
        context,
        node_types.get(edge.right, "other"),
        node_port_labels,
        node_port_prefix,
    )


_iso_client_attachment = _client_attachment


def _record_iso_client_edge_label(
    context: _svg_edge_labels_record.EdgeLabelContext,
    client_node: str,
    upstream_display: str,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    if "<->" in context.compact_label:
        return
    port_text = _client_port_text(context)
    node_port_labels.setdefault(client_node, f"{upstream_display}: {port_text}")
    node_port_prefix.setdefault(client_node, _shorten_prefix(upstream_display))


def _record_iso_device_edge_label(
    edge: Edge,
    context: _svg_edge_labels_record.EdgeLabelContext,
    right_type: str,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    upstream_name = _upstream_name_from_label(context) or context.left_name
    label_text = _infra_label_text(context, right_type, upstream_name=upstream_name)
    node_port_labels.setdefault(edge.right, label_text)
    node_port_prefix.setdefault(edge.right, _shorten_prefix(context.left_name))
