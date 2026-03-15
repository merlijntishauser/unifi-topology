"""Edge rendering for orthogonal SVG network diagrams."""

from __future__ import annotations

import math

from ..model.topology import Edge
from . import _svg_edge_labels_record, _svg_edge_shared
from .svg_theme import SvgOptions, SvgTheme

__all__ = [
    "_client_attachment",
    "_client_port_text",
    "_compute_elbow_path",
    "_edge_label_context",
    "_edge_opacity",
    "_edge_render_state",
    "_infra_label_text",
    "_record_client_label",
    "_record_edge_labels",
    "_record_infra_label",
    "_render_poe_icon",
    "_render_single_edge",
    "_render_standard_edge",
    "_render_svg_edges",
    "_render_vlan_endpoint_markers",
    "_render_vlan_striped_edge",
    "_upstream_name_from_label",
    "_vlan_data_attrs",
]

_client_attachment = _svg_edge_labels_record._client_attachment
_client_port_text = _svg_edge_labels_record._client_port_text
_edge_label_context = _svg_edge_labels_record._edge_label_context
_edge_opacity = _svg_edge_shared._edge_opacity
_edge_render_state = _svg_edge_shared._edge_render_state
_infra_label_text = _svg_edge_labels_record._infra_label_text
_render_vlan_endpoint_markers = _svg_edge_shared._render_vlan_endpoint_markers
_upstream_name_from_label = _svg_edge_labels_record._upstream_name_from_label
_vlan_data_attrs = _svg_edge_shared._vlan_data_attrs


def _render_vlan_striped_edge(
    lines: list[str],
    path: str,
    vlans: tuple[int, ...],
    theme: SvgTheme,
    base_width: int,
    is_wireless: bool,
    extra_attrs: str,
    opacity: float = 1.0,
) -> None:
    """Render an edge with striped VLAN colors and glow effect."""
    if not vlans:
        return
    num_vlans = len(vlans)
    segment_len = 12  # Length of each colored segment
    total_pattern = segment_len * num_vlans
    gap_len = total_pattern - segment_len  # Gap is rest of pattern
    opacity_attr = f' opacity="{opacity}"' if opacity < 1.0 else ""

    # Render glow layer behind the edge
    glow_color = theme.vlan_color(vlans[0])
    glow_width = base_width * 3
    glow_opacity = 0.25 * opacity  # Scale glow with edge opacity
    lines.append(
        f'<path d="{path}" stroke="{glow_color}" stroke-width="{glow_width}" '
        f'fill="none" opacity="{glow_opacity}" filter="url(#edge-glow)" {extra_attrs}/>'
    )

    for i, vlan_id in enumerate(vlans):
        color = theme.vlan_color(vlan_id)
        offset = -i * segment_len
        dash = f'stroke-dasharray="{segment_len} {gap_len}"'
        if is_wireless:
            # For wireless, use smaller dashes within the segment
            dash = f'stroke-dasharray="4 2 4 {gap_len + 2}"'
        lines.append(
            f'<path d="{path}" stroke="{color}" stroke-width="{base_width}" '
            f'fill="none" {dash} stroke-dashoffset="{offset}"{opacity_attr} {extra_attrs}/>'
        )


def _compute_elbow_path(
    src_cx: float, src_bottom: float, dst_cx: float, dst_top: float, mid_y: float
) -> str:
    """Compute SVG path for an elbow connector between two nodes."""
    if math.isclose(src_cx, dst_cx, abs_tol=0.01):
        elbow_x = src_cx + 0.5
        return (
            f"M {src_cx} {src_bottom} L {src_cx} {mid_y} "
            f"L {elbow_x} {mid_y} L {dst_cx} {mid_y} L {dst_cx} {dst_top}"
        )
    return f"M {src_cx} {src_bottom} L {src_cx} {mid_y} L {dst_cx} {mid_y} L {dst_cx} {dst_top}"


def _render_poe_icon(
    lines: list[str], dst_cx: float, mid_y: float, dst_top: float, theme: SvgTheme
) -> None:
    """Render PoE lightning bolt icon on an edge."""
    poe_size = 16
    icon_x = dst_cx - poe_size / 2
    icon_center_y = mid_y + 0.8 * (dst_top - mid_y)
    icon_y = icon_center_y - poe_size / 2
    lines.append(
        f'<use href="#poe-bolt" x="{icon_x}" y="{icon_y}" '
        f'width="{poe_size}" height="{poe_size}" '
        f'fill="{theme.poe_fill}" stroke="{theme.poe_stroke}" stroke-width="0.5"/>'
    )


def _render_standard_edge(
    lines: list[str],
    path: str,
    edge: Edge,
    opacity_attr: str,
    base_attrs: str,
) -> None:
    """Render a standard edge (no VLAN coloring)."""
    color = "url(#link-poe)" if edge.poe else "url(#link-standard)"
    dash = ' stroke-dasharray="6 4"' if edge.wireless else ""
    width_px = 2 if edge.poe else 1
    lines.append(
        f'<path d="{path}" stroke="{color}" stroke-width="{width_px}" '
        f'fill="none"{dash}{opacity_attr} {base_attrs}/>'
    )


def _render_single_edge(
    lines: list[str],
    edge: Edge,
    positions: dict[str, tuple[float, float]],
    node_types: dict[str, str],
    options: SvgOptions,
    theme: SvgTheme,
    max_vlan_colors: int | None,
) -> None:
    """Render a single edge with coordinates, attributes, and optional VLAN styling."""
    src_x, src_y = positions[edge.left]
    dst_x, dst_y = positions[edge.right]
    src_cx = src_x + options.node_width / 2
    dst_cx = dst_x + options.node_width / 2
    src_bottom = src_y + options.node_height
    dst_top = dst_y
    mid_y = (src_bottom + dst_top) / 2
    width_px = 2 if edge.poe else 1

    path = _compute_elbow_path(src_cx, src_bottom, dst_cx, dst_top, mid_y)
    state = _edge_render_state(edge, node_types, max_vlan_colors=max_vlan_colors)

    if state.display_vlans:
        _render_vlan_striped_edge(
            lines,
            path,
            state.display_vlans,
            theme,
            width_px,
            edge.wireless,
            state.base_attrs,
            state.opacity,
        )
        _render_vlan_endpoint_markers(lines, dst_cx, dst_top + 4, state.display_vlans, theme)
    else:
        _render_standard_edge(lines, path, edge, state.opacity_attr, state.base_attrs)

    if edge.poe:
        _render_poe_icon(lines, dst_cx, mid_y, dst_top, theme)


def _render_svg_edges(
    lines: list[str],
    edges: list[Edge],
    positions: dict[str, tuple[float, float]],
    node_types: dict[str, str],
    options: SvgOptions,
    theme: SvgTheme,
    max_vlan_colors: int | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    node_port_labels: dict[str, str] = {}
    node_port_prefix: dict[str, str] = {}
    for edge in edges:
        _record_edge_labels(edge, node_types, node_port_labels, node_port_prefix)
    for edge in sorted(edges, key=lambda item: item.poe):
        if edge.left not in positions or edge.right not in positions:
            continue
        _render_single_edge(lines, edge, positions, node_types, options, theme, max_vlan_colors)
    return node_port_labels, node_port_prefix


def _record_client_label(
    context: _svg_edge_labels_record.EdgeLabelContext,
    client_node: str,
    upstream_node: str,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    """Record port label for a client edge."""
    if "<->" in context.compact_label:
        return
    port_text = _client_port_text(context)
    upstream_name = _upstream_name_from_label(context) or upstream_node
    node_port_labels.setdefault(client_node, f"{upstream_name}: {port_text}")
    node_port_prefix.setdefault(client_node, upstream_name)


def _record_infra_label(
    edge: Edge,
    context: _svg_edge_labels_record.EdgeLabelContext,
    right_type: str,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
) -> None:
    """Record port label for an infrastructure edge."""
    upstream_name = _upstream_name_from_label(context) or edge.left
    label_text = _infra_label_text(context, right_type, upstream_name=upstream_name)
    node_port_labels.setdefault(edge.right, label_text)
    node_port_prefix.setdefault(edge.right, upstream_name)


def _record_edge_labels(
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
        client_node, upstream_node = client_attachment
        _record_client_label(
            context, client_node, upstream_node, node_port_labels, node_port_prefix
        )
        return
    _record_infra_label(
        edge,
        context,
        node_types.get(edge.right, "other"),
        node_port_labels,
        node_port_prefix,
    )
