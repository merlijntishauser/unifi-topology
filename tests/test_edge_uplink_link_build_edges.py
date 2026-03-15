"""Tests for uplink-link behavior through edge building."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import build_edges
from unifi_topology.model.topology import UplinkInfo


def test_build_edges_uplink_only_unifi_skips_unknown_upstream():
    switch = make_device(
        "Switch",
        "aa",
        uplink=UplinkInfo(mac=None, name="Unknown Device", port=1),
    )
    assert build_edges([switch], only_unifi=True) == []


def test_build_edges_uses_last_uplink_when_uplink_missing():
    gateway = make_device("Gateway", "bb", device_type="gateway")
    switch = make_device(
        "Switch",
        "aa",
        last_uplink=UplinkInfo(mac="bb", name="Gateway", port=2),
    )
    edges = build_edges([gateway, switch], include_ports=True)
    assert len(edges) == 1
    assert edges[0].label == "Gateway: Port 2 <-> Switch: ?"
