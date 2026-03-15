"""Private helpers shared by orthogonal and isometric edge renderers."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as _escape_html

from ..model.topology import Edge
from .svg_theme import SvgTheme


def _vlan_data_attrs(edge: Edge) -> str:
    """Generate VLAN data attributes for an edge."""
    attrs = []
    if edge.vlans:
        attrs.append(f'data-vlans="{",".join(str(v) for v in edge.vlans)}"')
    if edge.active_vlans:
        attrs.append(f'data-active-vlans="{",".join(str(v) for v in edge.active_vlans)}"')
    if edge.is_trunk:
        attrs.append('data-trunk="true"')
    return " ".join(attrs)


def _edge_opacity(node_types: dict[str, str], edge: Edge) -> float:
    """Return opacity for edge based on endpoint types."""
    left_type = node_types.get(edge.left, "other")
    right_type = node_types.get(edge.right, "other")
    if right_type == "client" or left_type == "client":
        return 0.5
    return 1.0


def _edge_base_attrs(edge: Edge) -> str:
    left_attr = _escape_html(edge.left, quote=True)
    right_attr = _escape_html(edge.right, quote=True)
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
