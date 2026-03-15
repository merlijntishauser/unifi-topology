"""Public API contract tests for the top-level package."""

from __future__ import annotations

import inspect

import unifi_topology as ut


def _sample_raw_devices() -> list[dict[str, object]]:
    return [
        {
            "name": "Gateway",
            "model_name": "Gateway",
            "model": "UDM",
            "mac": "aa:aa:aa:aa:aa:aa",
            "ip": "192.168.1.1",
            "type": "gateway",
            "lldp_info": [],
            "port_table": [
                {
                    "port_idx": 1,
                    "name": "Port 1",
                    "ifname": "eth0",
                    "speed": 1000,
                }
            ],
            "network_table": [],
        },
        {
            "name": "Switch",
            "model_name": "Switch",
            "model": "USW-8",
            "mac": "bb:bb:bb:bb:bb:bb",
            "ip": "192.168.1.2",
            "type": "switch",
            "lldp_info": [
                {
                    "chassis_id": "aa:aa:aa:aa:aa:aa",
                    "port_id": "Port 1",
                    "local_port_name": "Port 1",
                }
            ],
            "port_table": [
                {
                    "port_idx": 1,
                    "name": "Port 1",
                    "ifname": "port1",
                    "speed": 1000,
                }
            ],
            "uplink": {
                "uplink_mac": "aa:aa:aa:aa:aa:aa",
                "uplink_device_name": "Gateway",
                "uplink_remote_port": 1,
            },
            "network_table": [],
        },
    ]


def test_top_level_exports_resolve():
    for name in ut.__all__:
        assert hasattr(ut, name), name
        assert getattr(ut, name) is not None, name


def test_public_topology_signature_stays_compatible():
    signature = inspect.signature(ut.build_topology)
    parameters = list(signature.parameters.values())

    assert [parameter.name for parameter in parameters] == [
        "devices",
        "include_ports",
        "only_unifi",
        "gateways",
    ]
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters[1:]
    )


def test_public_render_signatures_stay_compatible():
    render_svg_signature = inspect.signature(ut.render_svg)
    render_svg_parameters = list(render_svg_signature.parameters.values())
    assert render_svg_parameters[0].name == "edges"
    assert render_svg_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert render_svg_parameters[1].name == "node_types"
    assert render_svg_parameters[1].kind is inspect.Parameter.KEYWORD_ONLY

    render_dual_signature = inspect.signature(ut.render_dual)
    render_dual_parameters = list(render_dual_signature.parameters.values())
    assert render_dual_parameters[0].name == "edges"
    assert render_dual_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert render_dual_parameters[1].name == "node_types"
    assert render_dual_parameters[1].kind is inspect.Parameter.KEYWORD_ONLY


def test_topology_result_fields_stay_public():
    fields = ut.TopologyResult.__dataclass_fields__
    assert "raw_edges" in fields
    assert "tree_edges" in fields


def test_readme_style_render_workflow_smoke():
    devices = ut.normalize_devices(_sample_raw_devices())
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
