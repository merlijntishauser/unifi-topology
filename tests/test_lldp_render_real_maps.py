"""Integration test: render_lldp_md must render real MAC-keyed builder output.

Regression guard for the v2 MAC-id migration, where port/client maps became
MAC-keyed but the renderer looked them up by device name.
"""

from __future__ import annotations

from unifi_topology.model.topology import Device, PortInfo, UplinkInfo
from unifi_topology.render.lldp import render_lldp_md

_SWITCH_MAC = "aa:bb:cc:dd:ee:01"
_AP_MAC = "aa:bb:cc:dd:ee:02"


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
        "mac": "cc:dd:ee:ff:00:11",
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


def test_port_table_shows_connected_device_name():
    output = render_lldp_md([_switch(), _ap()], include_ports=True)
    row = _port_row(output, "Port 5")
    assert "AccessPoint" in row


def test_port_table_shows_connected_client_name():
    output = render_lldp_md(
        [_switch(), _ap()],
        clients=[_client()],
        include_ports=True,
        show_clients=True,
    )
    row = _port_row(output, "Port 3")
    assert "Laptop" in row
    assert "cc:dd:ee:ff:00:11" not in row


def test_ports_section_does_not_duplicate_details_table():
    output = render_lldp_md([_switch()], include_ports=True)
    # The device details table must appear once, not once per section.
    assert output.count("Details") == 1
