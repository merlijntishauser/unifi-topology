"""Private helpers for isometric edge label recording."""

from __future__ import annotations

from ..model.topology import Edge
from . import _svg_edge_labels_record
from .svg_labels import _shorten_prefix

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
) -> None:
    for edge in edges:
        _record_iso_edge_label(edge, node_types, node_port_labels, node_port_prefix)


def _record_iso_edge_label(
    edge: Edge,
    node_types: dict[str, str],
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    context = _edge_label_context(edge)
    if context is None:
        return
    client_attachment = _client_attachment(edge, node_types)
    if client_attachment is not None:
        _record_iso_client_edge_label(
            context,
            client_attachment,
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
    client_attachment: tuple[str, str],
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    client_node, upstream_node = client_attachment
    if "<->" in context.compact_label:
        return
    port_text = _client_port_text(context)
    node_port_labels.setdefault(client_node, f"{upstream_node}: {port_text}")
    node_port_prefix.setdefault(client_node, _shorten_prefix(upstream_node))


def _record_iso_device_edge_label(
    edge: Edge,
    context: _svg_edge_labels_record.EdgeLabelContext,
    right_type: str,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    upstream_name = _upstream_name_from_label(context) or edge.left
    label_text = _infra_label_text(context, right_type, upstream_name=upstream_name)
    node_port_labels.setdefault(edge.right, label_text)
    node_port_prefix.setdefault(edge.right, _shorten_prefix(edge.left))
