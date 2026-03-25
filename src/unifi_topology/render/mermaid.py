"""Mermaid diagram rendering."""

from __future__ import annotations

import json
from collections.abc import Iterable

from ..model.topology import Edge, WanInfo, WanInterface
from ._templating import render_template
from .mermaid_theme import DEFAULT_THEME, MermaidTheme, class_defs


def _escape(label: str) -> str:
    normalized = label.replace("\r\n", "\n").replace("\r", "\n")
    escaped = normalized.replace("\\", "\\\\").replace("\n", "\\n")
    return escaped.replace('"', '\\"')


def _normalize_chars(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())


def _slugify(value: str) -> str:
    slug = _normalize_chars(value).strip("_")
    if not slug or slug[0].isdigit():
        slug = f"n_{slug}" if slug else "n"
    return slug


def _assign_id(name: str, id_map: dict[str, str], used: set[str]) -> None:
    if name in id_map:
        return
    base = _slugify(name)
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}_{counter}"
        counter += 1
    id_map[name] = candidate
    used.add(candidate)


def _build_id_map(edges: Iterable[Edge], nodes: Iterable[str]) -> dict[str, str]:
    id_map: dict[str, str] = {}
    used: set[str] = set()
    for node in nodes:
        _assign_id(node, id_map, used)
    for edge in edges:
        _assign_id(edge.left, id_map, used)
        _assign_id(edge.right, id_map, used)
    return id_map


def _node_ref(display_name: str, node_id: str) -> str:
    return f'{node_id}["{_escape(display_name)}"]'


def _group_nodes(groups: dict[str, list[str]] | None) -> list[str]:
    if not groups:
        return []
    nodes: list[str] = []
    for members in groups.values():
        nodes.extend(members)
    return nodes


def _render_group_sections(
    lines: list[str],
    groups: dict[str, list[str]],
    *,
    group_order: list[str] | None,
    id_map: dict[str, str],
    node_names: dict[str, str] | None = None,
) -> None:
    ordered = group_order or list(groups.keys())
    for group_name in ordered:
        members = groups.get(group_name, [])
        if not members:
            continue
        _render_single_group(lines, group_name, members, id_map, node_names=node_names)


def _render_single_group(
    lines: list[str],
    group_name: str,
    members: list[str],
    id_map: dict[str, str],
    node_names: dict[str, str] | None = None,
) -> None:
    names = node_names or {}
    group_id = _slugify(f"group_{group_name}")
    label = group_name.replace("_", " ").title()
    lines.append(f'  subgraph {group_id}["{_escape(label)}"];')
    for member in members:
        display = names.get(member, member)
        lines.append(f"    {_node_ref(display, id_map[member])};")
    lines.append("  end")


def _format_vlan_suffix(active_vlans: tuple[int, ...]) -> str:
    """Format VLAN suffix for edge labels."""
    if not active_vlans:
        return ""
    vlan_str = ",".join(f"V{v}" for v in sorted(active_vlans))
    return f" [{vlan_str}]"


def _edge_node_refs(
    edge: Edge,
    id_map: dict[str, str],
    use_node_labels: bool,
    node_names: dict[str, str] | None,
) -> tuple[str, str]:
    if not use_node_labels:
        return id_map[edge.left], id_map[edge.right]
    names = node_names or {}
    left = _node_ref(names.get(edge.left, edge.left), id_map[edge.left])
    right = _node_ref(names.get(edge.right, edge.right), id_map[edge.right])
    return left, right


def _render_single_edge(
    lines: list[str],
    edge: Edge,
    *,
    id_map: dict[str, str],
    use_node_labels: bool,
    node_names: dict[str, str] | None = None,
) -> None:
    left, right = _edge_node_refs(edge, id_map, use_node_labels, node_names)
    vlan_suffix = _format_vlan_suffix(edge.active_vlans)
    if edge.label or vlan_suffix:
        label = _escape(f"{edge.label or ''}{vlan_suffix}".strip())
        lines.append(f'  {left} ---|"{label}"| {right};')
    else:
        lines.append(f"  {left} --- {right};")


def _render_edge_lines(
    lines: list[str],
    edges: list[Edge],
    *,
    id_map: dict[str, str],
    use_node_labels: bool,
    node_names: dict[str, str] | None = None,
) -> tuple[list[int], list[int]]:
    poe_links: list[int] = []
    wireless_links: list[int] = []
    for index, edge in enumerate(edges):
        _render_single_edge(
            lines, edge, id_map=id_map, use_node_labels=use_node_labels, node_names=node_names
        )
        if edge.poe:
            poe_links.append(index)
        if edge.wireless:
            wireless_links.append(index)
    return poe_links, wireless_links


def _render_node_classes(
    lines: list[str],
    *,
    node_types: dict[str, str],
    id_map: dict[str, str],
    theme: MermaidTheme,
) -> None:
    class_map = {
        "gateway": "node_gateway",
        "switch": "node_switch",
        "ap": "node_ap",
        "client": "node_client",
        "other": "node_other",
    }
    for name, node_type in node_types.items():
        class_name = class_map.get(node_type, "node_other")
        node_id = id_map.get(name)
        if node_id:
            lines.append(f"  class {node_id} {class_name};")
    lines.extend(class_defs(theme))


def _render_link_styles(
    lines: list[str],
    *,
    poe_links: list[int],
    wireless_links: list[int],
    theme: MermaidTheme,
) -> None:
    for index in poe_links:
        lines.append(
            "  linkStyle "
            f"{index} stroke:{theme.poe_link},stroke-width:{theme.poe_link_width}px,"
            f"arrowhead:{theme.poe_link_arrow};"
        )
    for index in wireless_links:
        lines.append(f"  linkStyle {index} stroke-dasharray: 5 4;")


def _format_wan_speed(speed_mbps: int | None) -> str | None:
    if speed_mbps is None or speed_mbps == 0:
        return None
    if speed_mbps >= 1000:
        return _format_gbps(speed_mbps)
    return f"{speed_mbps}MbE"


def _format_gbps(speed_mbps: int) -> str:
    gbps = speed_mbps / 1000
    if gbps == int(gbps):
        return f"{int(gbps)}GbE"
    return f"{gbps:.1f}GbE"


def _wan_interface_label(wan: WanInterface, prefix: str, *, is_dual: bool) -> str:
    base = wan.label or prefix
    return f"{prefix}: {base}" if is_dual else base


def _format_wan_interface(wan: WanInterface, prefix: str, *, is_dual: bool) -> list[str]:
    """Format a single WAN interface for a Mermaid node label."""
    parts: list[str] = [_wan_interface_label(wan, prefix, is_dual=is_dual)]
    speed_parts = _wan_speed_parts(wan)
    if speed_parts:
        parts.append(" / ".join(speed_parts))
    if not wan.enabled and is_dual:
        parts.append("(disabled)")
    return parts


def _wan_speed_parts(wan: WanInterface) -> list[str]:
    speed_parts: list[str] = []
    if wan.link_speed and wan.enabled:
        formatted = _format_wan_speed(wan.link_speed)
        if formatted:
            speed_parts.append(formatted)
    if wan.isp_speed:
        speed_parts.append(wan.isp_speed)
    return speed_parts


def _wan_ip_label(wan: WanInterface) -> str | None:
    if wan.public_ip and wan.public_ip != wan.ip_address:
        return wan.public_ip
    return wan.ip_address


def _wan_label_parts(wan_info: WanInfo) -> list[str]:
    parts: list[str] = []
    is_dual = wan_info.wan2 is not None
    if wan_info.wan1:
        parts.extend(_format_wan_interface(wan_info.wan1, "WAN1", is_dual=is_dual))
    if wan_info.wan2:
        if parts:
            parts.append("|")
        parts.extend(_format_wan_interface(wan_info.wan2, "WAN2", is_dual=is_dual))
    return parts


def _build_wan_node_label(wan_info: WanInfo) -> str:
    """Build a concise label for the WAN node."""
    parts = _wan_label_parts(wan_info)
    if wan_info.wan1:
        ip_label = _wan_ip_label(wan_info.wan1)
        if ip_label:
            parts.append(ip_label)
    return " ".join(parts)


def _find_gateway_name(node_types: dict[str, str] | None) -> str | None:
    """Find the gateway node name to connect the WAN node to."""
    if not node_types:
        return None
    for name, ntype in node_types.items():
        if ntype == "gateway":
            return name
    return None


def _render_wan_node(
    lines: list[str],
    wan_info: WanInfo,
    gateway_id: str,
    *,
    id_map: dict[str, str],
    use_node_labels: bool,
    node_names: dict[str, str] | None = None,
) -> None:
    """Render a WAN upstream node connected to the gateway."""
    names = node_names or {}
    wan_id = id_map["__wan__"]
    label = _escape(_build_wan_node_label(wan_info))
    lines.append(f'  {wan_id}(["{label}"]);')
    gateway_display = names.get(gateway_id, gateway_id)
    gw = _node_ref(gateway_display, id_map[gateway_id]) if use_node_labels else id_map[gateway_id]
    lines.append(f"  {wan_id} --- {gw};")
    lines.append(f"  class {wan_id} node_wan;")


def _build_theme_init(theme: MermaidTheme) -> dict[str, object]:
    theme_vars: dict[str, object] = {}
    if theme.edge_label_border:
        theme_vars["edgeLabelBorderColor"] = theme.edge_label_border
    if theme.edge_label_border_width:
        theme_vars["edgeLabelBorderWidth"] = theme.edge_label_border_width
    return theme_vars


def _resolve_wan_gateway(
    wan_info: WanInfo | None,
    node_types: dict[str, str] | None,
) -> str | None:
    if not wan_info:
        return None
    return _find_gateway_name(node_types)


def render_mermaid(
    edges: Iterable[Edge],
    direction: str = "LR",
    *,
    groups: dict[str, list[str]] | None = None,
    group_order: list[str] | None = None,
    node_types: dict[str, str] | None = None,
    node_names: dict[str, str] | None = None,
    theme: MermaidTheme = DEFAULT_THEME,
    wan_info: WanInfo | None = None,
) -> str:
    edge_list = list(edges)
    gateway_id = _resolve_wan_gateway(wan_info, node_types)
    extra_nodes = ["__wan__"] if gateway_id else []
    id_map = _build_id_map(edge_list, [*_group_nodes(groups), *extra_nodes])
    lines = _build_mermaid_header(direction, theme)
    _add_wan_section(
        lines, wan_info, gateway_id, id_map=id_map, groups=groups, node_names=node_names
    )
    _add_groups_and_edges(
        lines, edge_list, groups, group_order, node_types, id_map, theme, node_names=node_names
    )
    return "\n".join(lines) + "\n"


def _add_groups_and_edges(
    lines: list[str],
    edge_list: list[Edge],
    groups: dict[str, list[str]] | None,
    group_order: list[str] | None,
    node_types: dict[str, str] | None,
    id_map: dict[str, str],
    theme: MermaidTheme,
    node_names: dict[str, str] | None = None,
) -> None:
    if groups:
        _render_group_sections(
            lines, groups, group_order=group_order, id_map=id_map, node_names=node_names
        )
    use_node_labels = not groups
    poe_links, wireless_links = _render_edge_lines(
        lines, edge_list, id_map=id_map, use_node_labels=use_node_labels, node_names=node_names
    )
    if node_types:
        _render_node_classes(lines, node_types=node_types, id_map=id_map, theme=theme)
    _render_link_styles(lines, poe_links=poe_links, wireless_links=wireless_links, theme=theme)


def _build_mermaid_header(direction: str, theme: MermaidTheme) -> list[str]:
    lines: list[str] = []
    theme_vars = _build_theme_init(theme)
    if theme_vars:
        lines.append(f'%%{{init: {{"themeVariables": {json.dumps(theme_vars)}}}}}%%')
    lines.append(f"graph {direction}")
    return lines


def _add_wan_section(
    lines: list[str],
    wan_info: WanInfo | None,
    gateway_id: str | None,
    *,
    id_map: dict[str, str],
    groups: dict[str, list[str]] | None,
    node_names: dict[str, str] | None = None,
) -> None:
    if wan_info and gateway_id:
        _render_wan_node(
            lines,
            wan_info,
            gateway_id,
            id_map=id_map,
            use_node_labels=not groups,
            node_names=node_names,
        )


def render_legend(theme: MermaidTheme = DEFAULT_THEME, *, legend_scale: float = 1.0) -> str:
    scale = legend_scale if legend_scale > 0 else 1.0
    return (
        render_template(
            "mermaid_legend.mmd.j2",
            node_spacing=max(10, round(50 * scale)),
            rank_spacing=max(10, round(50 * scale)),
            legend_font_size=max(7, round(10 * scale)),
            node_padding=max(4, round(12 * scale)),
            class_defs="\n".join(class_defs(theme)),
            poe_link=theme.poe_link,
            poe_link_width=max(1, round(theme.poe_link_width * scale)),
            poe_link_arrow=theme.poe_link_arrow,
            standard_link=theme.standard_link,
            standard_link_width=max(1, round(theme.standard_link_width * scale)),
            standard_link_arrow=theme.standard_link_arrow,
        ).rstrip()
        + "\n"
    )


def _build_swatch_row(fill: str, stroke: str, label: str) -> dict[str, object]:
    return {"kind": "swatch", "fill": fill, "stroke": stroke, "label": label}


def _build_line_row(
    theme: MermaidTheme,
    *,
    color: str,
    width: int,
    dashed: bool,
    label: str,
    bolt: bool,
) -> dict[str, object]:
    return {
        "kind": "line",
        "color": color,
        "width": max(1, width),
        "dashed": dashed,
        "label": label,
        "bolt": bolt,
    }


def _legend_compact_rows(theme: MermaidTheme) -> list[dict[str, object]]:
    return [
        _build_swatch_row(theme.node_wan[0], theme.node_wan[1], "WAN"),
        _build_swatch_row(theme.node_gateway[0], theme.node_gateway[1], "Gateway"),
        _build_swatch_row(theme.node_switch[0], theme.node_switch[1], "Switch"),
        _build_swatch_row(theme.node_ap[0], theme.node_ap[1], "AP"),
        _build_swatch_row(theme.node_client[0], theme.node_client[1], "Client"),
        _build_swatch_row(theme.node_other[0], theme.node_other[1], "Other"),
        _build_line_row(
            theme,
            color=theme.poe_link,
            width=theme.poe_link_width,
            dashed=False,
            label="PoE",
            bolt=True,
        ),
        _build_line_row(
            theme,
            color=theme.standard_link,
            width=theme.standard_link_width,
            dashed=False,
            label="Link",
            bolt=False,
        ),
        _build_line_row(
            theme,
            color=theme.standard_link,
            width=theme.standard_link_width,
            dashed=True,
            label="Wireless",
            bolt=False,
        ),
    ]


def render_legend_compact(theme: MermaidTheme = DEFAULT_THEME) -> str:
    return render_template("legend_compact.html.j2", rows=_legend_compact_rows(theme))
