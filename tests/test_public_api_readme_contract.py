"""README-style public API contract smoke tests."""

from __future__ import annotations

import unifi_topology as ut
from tests.public_api_contract_helpers import sample_raw_devices


def test_readme_style_render_workflow_smoke():
    devices = ut.normalize_devices(sample_raw_devices())
    node_types = ut.build_node_type_map(devices)
    gateways = [name for name, node_type in node_types.items() if node_type == "gateway"]
    topology = ut.build_topology(
        devices,
        include_ports=True,
        only_unifi=False,
        gateways=gateways,
    )
    gateway = next((device for device in devices if node_types.get(device.name) == "gateway"), None)
    wan_info = ut.extract_wan_info(gateway) if gateway else None
    theme = ut.resolve_svg_themes(theme_name="unifi")

    svg = ut.render_svg(
        topology.tree_edges or topology.raw_edges,
        node_types=node_types,
        theme=theme,
        options=ut.SvgOptions(),
        wan_info=wan_info,
    )

    assert "<svg" in svg
    assert "Gateway" in svg
    assert "Switch" in svg
