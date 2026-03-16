"""Tests for Mermaid diagram rendering."""

from unifi_topology.model.topology import Edge, WanInfo, WanInterface
from unifi_topology.render.mermaid import render_legend, render_legend_compact, render_mermaid
from unifi_topology.render.mermaid_theme import DEFAULT_THEME


def test_render_mermaid_uses_ids_with_labels():
    output = render_mermaid([Edge("AP Wifi6 tuinhuis", "Core Switch")])
    assert 'ap_wifi6_tuinhuis["AP Wifi6 tuinhuis"]' in output


def test_render_mermaid_includes_edge_label():
    output = render_mermaid([Edge("A", "B", label="Port 1")])
    assert '---|"Port 1"|' in output


def test_render_mermaid_styles_poe_links():
    output = render_mermaid([Edge("A", "B", poe=True)])
    assert "linkStyle 0 stroke:#1e88e5" in output


def test_render_mermaid_styles_wireless_links():
    output = render_mermaid([Edge("A", "B", wireless=True)])
    assert "stroke-dasharray: 5 4" in output


def test_render_legend_outputs_subgraph():
    output = render_legend()
    assert "subgraph legend" in output


def test_render_mermaid_grouped_uses_semicolons():
    output = render_mermaid(
        [Edge("A", "B")],
        groups={"group": ["A", "B"]},
        group_order=["group"],
        node_types={"A": "gateway", "B": "switch"},
    )
    lines = output.splitlines()
    assert '  subgraph group_group["Group"];' in lines
    assert any(line.endswith(";") for line in lines if "---" in line)
    assert any(line.endswith(";") for line in lines if line.strip().startswith("class "))


def test_render_legend_link_inside_subgraph():
    output = render_legend().splitlines()
    end_line = "  end"
    assert "    legend_poe_a ---|⚡| legend_poe_b;" in output
    assert output.index("    legend_poe_a ---|⚡| legend_poe_b;") < output.index(end_line)
    assert "    legend_no_poe_a --- legend_no_poe_b;" in output
    assert "    linkStyle 0 arrowhead:none;" in output
    assert "    linkStyle 1 arrowhead:none;" in output


def test_render_legend_subgraph_ends_with_semicolon():
    output = render_legend().splitlines()
    assert '  subgraph legend["Legend"];' in output


def test_render_legend_link_style_default():
    output = render_legend().splitlines()
    assert "  linkStyle 0 stroke:#1e88e5,stroke-width:2px,arrowhead:none;" in output
    assert "  linkStyle 1 stroke:#2ecc71,stroke-width:2px,arrowhead:none;" in output


def test_render_legend_class_lines_end_with_semicolon():
    output = render_legend().splitlines()
    assert "  class legend_gateway node_gateway;" in output


def test_render_legend_compact_outputs_table():
    output = render_legend_compact()
    assert '<table class="unifi-legend-table">' in output
    assert "background:#ffe3b3" in output
    assert "Link</span>" in output


def test_render_mermaid_renders_group_subgraph():
    output = render_mermaid([Edge("Gateway", "Switch")], groups={"gateway": ["Gateway"]})
    assert "subgraph group_gateway" in output


def test_render_mermaid_assigns_class_for_node_types():
    output = render_mermaid([Edge("A", "B")], node_types={"A": "gateway"})
    assert "class a node_gateway" in output


def test_render_mermaid_escapes_quotes():
    output = render_mermaid([Edge('A "1"', "B")])
    assert '\\"' in output


def test_render_mermaid_escapes_backslashes():
    output = render_mermaid([Edge("A \\ 1", "B")])
    assert "\\\\" in output


def test_render_mermaid_escapes_newlines():
    output = render_mermaid([Edge("Line 1\nLine 2", "B")])
    assert "\\n" in output


def test_slugify_digit_prefix():
    output = render_mermaid([Edge("1stFloor", "B")])
    assert "n_1stfloor" in output


def test_slugify_empty_name():
    output = render_mermaid([Edge("   ", "B")])
    assert "n ---" in output or "n[" in output


def test_assign_id_collision():
    output = render_mermaid(
        [Edge("A-B", "A_B")],
    )
    assert "a_b_2" in output


def test_group_order_skips_empty_group():
    output = render_mermaid(
        [Edge("A", "B")],
        groups={"filled": ["A"], "empty": []},
        group_order=["empty", "filled"],
    )
    assert "group_empty" not in output
    assert "group_filled" in output


def test_edge_with_active_vlans():
    output = render_mermaid([Edge("A", "B", label="Port 1", active_vlans=(10, 20))])
    assert "[V10,V20]" in output


def test_edge_with_vlans_only():
    output = render_mermaid([Edge("A", "B", active_vlans=(42,))])
    assert "[V42]" in output


def test_wan_single_interface():
    wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "__wan__" not in output
    assert "wan" in output.lower()
    assert "1GbE" in output
    assert "node_wan" in output


def test_wan_dual_interface():
    wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
    wan2 = WanInterface(port_idx=2, link_speed=None, ip_address=None, enabled=False, label="Backup")
    wan_info = WanInfo(wan1=wan1, wan2=wan2)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "WAN1" in output
    assert "WAN2" in output
    assert "(disabled)" in output


def test_wan_interface_with_isp_speed():
    wan1 = WanInterface(
        port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True, isp_speed="500/100"
    )
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "500/100" in output


def test_wan_speed_mbps():
    wan1 = WanInterface(port_idx=1, link_speed=100, ip_address=None, enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "100MbE" in output


def test_wan_speed_fractional_gbps():
    wan1 = WanInterface(port_idx=1, link_speed=2500, ip_address=None, enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "2.5GbE" in output


def test_wan_ignored_without_gateway_node_type():
    wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address=None, enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        wan_info=wan_info,
    )
    assert "node_wan" not in output


def test_wan_with_groups():
    wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address=None, enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        groups={"core": ["GW", "SW"]},
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "node_wan" in output
    assert "gw" in output


def test_theme_edge_label_border():
    from dataclasses import replace

    theme = replace(DEFAULT_THEME, edge_label_border="#ff0000", edge_label_border_width=3)
    output = render_mermaid([Edge("A", "B")], theme=theme)
    assert "edgeLabelBorderColor" in output
    assert "#ff0000" in output
    assert "edgeLabelBorderWidth" in output


def test_wan_speed_zero_returns_no_speed():
    wan1 = WanInterface(port_idx=1, link_speed=0, ip_address=None, enabled=True)
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "GbE" not in output
    assert "MbE" not in output


def test_wan_interface_custom_label():
    wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address=None, enabled=True, label="Fiber")
    wan_info = WanInfo(wan1=wan1)
    output = render_mermaid(
        [Edge("GW", "SW")],
        node_types={"GW": "gateway", "SW": "switch"},
        wan_info=wan_info,
    )
    assert "Fiber" in output
