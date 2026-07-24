"""render_device_port_overview must render real MAC-keyed builder output.

Regression guard for issue #67: the device-port markdown table's Connected
column was always empty because MAC-keyed maps were filtered by display name.
"""

from __future__ import annotations

from unifi_topology.model.clients import build_client_port_map
from unifi_topology.model.edges import build_port_map
from unifi_topology.model.topology import Device, PortInfo, UplinkInfo
from unifi_topology.render.markdown import render_device_port_overview

_SWITCH_MAC = "aa:bb:cc:dd:ee:01"
_AP_MAC = "aa:bb:cc:dd:ee:02"
_CLIENT_MAC = "cc:dd:ee:ff:00:11"


def _port(idx: int) -> PortInfo:
    return PortInfo(
        port_idx=idx,
        name=f"Port {idx}",
        ifname=f"eth{idx}",
        speed=1000,
        aggregation_group=None,
        port_poe=False,
        poe_enable=False,
        poe_good=False,
        poe_power=None,
    )


def _switch() -> Device:
    return Device(
        name="Switch",
        model_name="",
        model="",
        mac=_SWITCH_MAC,
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[_port(3), _port(5)],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="",
    )


def _ap() -> Device:
    return Device(
        name="AccessPoint",
        model_name="",
        model="",
        mac=_AP_MAC,
        ip="",
        type="ap",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=UplinkInfo(mac=_SWITCH_MAC, name="Switch", port=5),
        last_uplink=None,
        version="",
    )


def _client() -> dict[str, object]:
    return {
        "mac": _CLIENT_MAC,
        "name": "Laptop",
        "is_wired": True,
        "sw_mac": _SWITCH_MAC,
        "sw_port": 3,
    }


def _port_row(output: str, port_label: str) -> str:
    for line in output.splitlines():
        if line.startswith(f"| {port_label} "):
            return line
    return ""


def test_connected_column_shows_peer_device_name():
    devices = [_switch(), _ap()]
    port_map = build_port_map(devices, only_unifi=False)
    output = render_device_port_overview(devices, port_map)
    row = _port_row(output, "Port 5")
    assert "AccessPoint" in row
    assert _AP_MAC not in row


def test_connected_column_shows_client_name_with_node_names():
    devices = [_switch(), _ap()]
    clients = [_client()]
    port_map = build_port_map(devices, only_unifi=False)
    client_ports = build_client_port_map(devices, clients, client_mode="wired")
    node_names = {_CLIENT_MAC: "Laptop"}
    output = render_device_port_overview(
        devices, port_map, client_ports=client_ports, node_names=node_names
    )
    row = _port_row(output, "Port 3")
    assert "Laptop" in row
    assert _CLIENT_MAC not in row
