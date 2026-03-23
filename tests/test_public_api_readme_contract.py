"""README-style public API contract smoke tests."""

from __future__ import annotations

import unifi_topology as ut
from tests.public_api_contract_helpers import sample_raw_devices
from unifi_topology.model.helpers import normalize_mac


def test_readme_style_render_workflow_smoke():
    devices = ut.normalize_devices(sample_raw_devices())
    node_types = ut.build_node_type_map(devices)
    # node_types keys are now MACs; find gateways by MAC
    gateways = [mac for mac, node_type in node_types.items() if node_type == "gateway"]
    topology = ut.build_topology(
        devices,
        include_ports=True,
        only_unifi=False,
        gateways=gateways,
    )
    node_names = topology.node_names
    gateway = next(
        (device for device in devices if node_types.get(normalize_mac(device.mac)) == "gateway"),
        None,
    )
    wan_info = ut.extract_wan_info(gateway) if gateway else None
    theme = ut.resolve_svg_themes(theme_name="unifi")

    svg = ut.render_svg(
        topology.tree_edges or topology.raw_edges,
        node_types=node_types,
        theme=theme,
        options=ut.SvgOptions(),
        wan_info=wan_info,
        node_names=node_names,
    )

    assert "<svg" in svg
    assert "Gateway" in svg
    assert "Switch" in svg
