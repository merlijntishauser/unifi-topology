"""Private orchestration helpers for orthogonal SVG rendering."""

from __future__ import annotations

from dataclasses import dataclass

from ..model.topology import Edge, VpnTunnel, WanInfo
from ._svg_render_common import _find_gateway_position, render_at_gateway
from .svg_layout import GroupBounds, _layout_grouped_nodes, _layout_nodes
from .svg_theme import SvgOptions, SvgTheme
from .svg_vpn import _render_vpn_tunnels, _vpn_box_height_estimate
from .svg_wan import _apply_wan_offset, _render_wan_upstream


@dataclass(frozen=True)
class SvgLayoutResult:
    positions: dict[str, tuple[float, float]]
    group_bounds_list: list[GroupBounds]
    width: float
    height: float
    use_grouped: bool


def _base_svg_layout(
    edges: list[Edge],
    node_types: dict[str, str],
    options: SvgOptions,
    groups: dict[str, list[str]] | None,
    group_order: list[str] | None,
) -> SvgLayoutResult:
    use_grouped = options.layout_mode == "grouped" and bool(groups)
    if use_grouped and groups:
        positions, group_bounds_list, width, height = _layout_grouped_nodes(
            edges,
            node_types,
            options,
            groups,
            group_order,
        )
        return SvgLayoutResult(
            positions=positions,
            group_bounds_list=group_bounds_list,
            width=float(width),
            height=float(height),
            use_grouped=True,
        )
    positions, width, height = _layout_nodes(edges, node_types, options)
    return SvgLayoutResult(
        positions=positions,
        group_bounds_list=[],
        width=float(width),
        height=float(height),
        use_grouped=False,
    )


def _apply_svg_overlay_layout(
    layout: SvgLayoutResult,
    *,
    wan_info: WanInfo | None,
    vpn_tunnels: list[VpnTunnel] | None,
    options: SvgOptions,
) -> SvgLayoutResult:
    positions = layout.positions
    group_bounds_list = layout.group_bounds_list
    height = layout.height

    if wan_info:
        wan_box_height = 36 + 3 * (options.font_size + 4) + 30 + 30
        positions, group_bounds_list, height = _apply_wan_offset(
            positions,
            group_bounds_list,
            height,
            wan_box_height,
        )

    if vpn_tunnels:
        height = height + _vpn_box_height_estimate(len(vpn_tunnels), options.font_size)

    return SvgLayoutResult(
        positions=positions,
        group_bounds_list=group_bounds_list,
        width=layout.width,
        height=float(height),
        use_grouped=layout.use_grouped,
    )


def compute_svg_layout(
    edges: list[Edge],
    node_types: dict[str, str],
    options: SvgOptions,
    groups: dict[str, list[str]] | None,
    group_order: list[str] | None,
    wan_info: WanInfo | None,
    vpn_tunnels: list[VpnTunnel] | None,
) -> SvgLayoutResult:
    layout = _base_svg_layout(edges, node_types, options, groups, group_order)
    return _apply_svg_overlay_layout(
        layout,
        wan_info=wan_info,
        vpn_tunnels=vpn_tunnels,
        options=options,
    )


def render_svg_gateway_overlays(
    *,
    lines: list[str],
    wan_info: WanInfo | None,
    vpn_tunnels: list[VpnTunnel] | None,
    node_types: dict[str, str],
    positions: dict[str, tuple[float, float]],
    options: SvgOptions,
    theme: SvgTheme,
    canvas_height: float,
) -> None:
    render_at_gateway(
        lines=lines,
        content=wan_info,
        node_types=node_types,
        positions=positions,
        find_gateway_position=_find_gateway_position,
        render=lambda doc_lines, info, gateway_pos: _render_wan_upstream(
            doc_lines,
            info,
            gateway_pos,
            options,
            theme,
        ),
    )
    render_at_gateway(
        lines=lines,
        content=vpn_tunnels,
        node_types=node_types,
        positions=positions,
        find_gateway_position=_find_gateway_position,
        render=lambda doc_lines, tunnels, gateway_pos: _render_vpn_tunnels(
            doc_lines,
            tunnels,
            gateway_pos,
            options,
            theme,
            canvas_height,
        ),
    )
