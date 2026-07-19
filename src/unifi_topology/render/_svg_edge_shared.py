"""Private helpers shared by orthogonal and isometric edge renderers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..model.topology import Edge
from .svg_labels import _escape_attr
from .svg_theme import SvgTheme


def _joined_vlans(vlans: tuple[int, ...]) -> str | None:
    if not vlans:
        return None
    return ",".join(str(vlan_id) for vlan_id in vlans)


def _edge_vlan_attrs(edge: Edge) -> list[str]:
    attrs = [
        f'{attr_name}="{value}"'
        for attr_name, value in (
            ("data-vlans", _joined_vlans(edge.vlans)),
            ("data-active-vlans", _joined_vlans(edge.active_vlans)),
        )
        if value is not None
    ]
    if edge.is_trunk:
        attrs.append('data-trunk="true"')
    return attrs


def _vlan_data_attrs(edge: Edge) -> str:
    """Generate VLAN data attributes for an edge."""
    return " ".join(_edge_vlan_attrs(edge))


def _edge_opacity(node_types: dict[str, str], edge: Edge) -> float:
    """Return opacity for edge based on endpoint types."""
    left_type = node_types.get(edge.left, "other")
    right_type = node_types.get(edge.right, "other")
    if right_type == "client" or left_type == "client":
        return 0.5
    return 1.0


def _edge_base_attrs(edge: Edge) -> str:
    left_attr = _escape_attr(edge.left)
    right_attr = _escape_attr(edge.right)
    base_attrs = f'data-edge-left="{left_attr}" data-edge-right="{right_attr}"'
    vlan_attrs = _vlan_data_attrs(edge)
    if vlan_attrs:
        return f"{base_attrs} {vlan_attrs}"
    return base_attrs


def _display_vlans(edge: Edge, max_vlan_colors: int | None) -> tuple[int, ...]:
    vlans = edge.active_vlans
    if max_vlan_colors and len(vlans) > max_vlan_colors:
        return vlans[:max_vlan_colors]
    return vlans


def _opacity_attr(opacity: float) -> str:
    if opacity < 1.0:
        return f' opacity="{opacity}"'
    return ""


@dataclass(frozen=True)
class EdgeRenderState:
    base_attrs: str
    display_vlans: tuple[int, ...]
    opacity: float
    opacity_attr: str


def _edge_render_state(
    edge: Edge,
    node_types: dict[str, str],
    *,
    max_vlan_colors: int | None,
) -> EdgeRenderState:
    opacity = _edge_opacity(node_types, edge)
    return EdgeRenderState(
        base_attrs=_edge_base_attrs(edge),
        display_vlans=_display_vlans(edge, max_vlan_colors),
        opacity=opacity,
        opacity_attr=_opacity_attr(opacity),
    )


def _render_vlan_endpoint_markers(
    lines: list[str],
    x: float,
    y: float,
    vlans: tuple[int, ...],
    theme: SvgTheme,
    marker_size: int = 6,
    max_markers: int = 4,
) -> None:
    """Render small colored squares showing active VLANs at an endpoint."""
    if not vlans:
        return
    for i, vlan_id in enumerate(vlans[:max_markers]):
        color = theme.vlan_color(vlan_id)
        marker_x = x - marker_size - 2
        marker_y = y + (i * (marker_size + 2))
        lines.append(
            f'<rect x="{marker_x}" y="{marker_y}" width="{marker_size}" '
            f'height="{marker_size}" fill="{color}" stroke="#fff" '
            f'stroke-width="0.5" rx="1" data-vlan="{vlan_id}">'
            f"<title>VLAN {vlan_id}</title></rect>"
        )


def _render_vlan_striped_edge_generic(
    lines: list[str],
    path: str,
    vlans: tuple[int, ...],
    theme: SvgTheme,
    base_width: int,
    is_wireless: bool,
    extra_attrs: str,
    opacity: float,
    *,
    segment_len: int,
    filter_id: str,
    line_attrs: str,
    wireless_dash: Callable[[int], str],
) -> None:
    """Render an edge striped by VLAN color with a glow layer.

    Shared by the orthogonal and isometric edge renderers, which differ only in
    the segment length, extra line attributes, glow-filter id, and the wireless
    dash pattern.
    """
    if not vlans:
        return
    num_vlans = len(vlans)
    total_pattern = segment_len * num_vlans
    gap_len = total_pattern - segment_len
    opacity_attr = f' opacity="{opacity}"' if opacity < 1.0 else ""

    glow_color = theme.vlan_color(vlans[0])
    glow_width = base_width * 3
    glow_opacity = 0.25 * opacity
    lines.append(
        f'<path d="{path}" stroke="{glow_color}" stroke-width="{glow_width}" '
        f'fill="none" {line_attrs}'
        f'opacity="{glow_opacity}" filter="url(#{filter_id})" {extra_attrs}/>'
    )

    for index, vlan_id in enumerate(vlans):
        color = theme.vlan_color(vlan_id)
        dash_offset = -index * segment_len
        dash = f'stroke-dasharray="{segment_len} {gap_len}"'
        if is_wireless:
            dash = f'stroke-dasharray="{wireless_dash(gap_len)}"'
        lines.append(
            f'<path d="{path}" stroke="{color}" stroke-width="{base_width}" '
            f'fill="none" {line_attrs}{dash} stroke-dashoffset="{dash_offset}"'
            f"{opacity_attr} {extra_attrs}/>"
        )
