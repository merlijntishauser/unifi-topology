"""Tests for edge and port-map discovery behavior."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device, make_port
from unifi_topology.model.edges import build_edges, build_port_map
from unifi_topology.model.helpers import normalize_mac
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import UplinkInfo


def test_build_edges_lldp_with_vlans():
    switch = make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[make_port(1, native_vlan=10, tagged_vlans=(20, 30))],
    )
    peer = make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch, peer])
    assert edges[0].vlans == (10, 20, 30)
    assert edges[0].is_trunk is True


def test_build_port_map_from_lldp():
    switch = make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
    )
    peer = make_device("Switch B", "aa:bb:cc:dd:ee:02")
    port_map = build_port_map([switch, peer])
    assert (normalize_mac("aa:bb:cc:dd:ee:01"), normalize_mac("aa:bb:cc:dd:ee:02")) in port_map


def test_build_port_map_from_uplink():
    gateway = make_device("Gateway", "bb", device_type="gateway")
    switch = make_device(
        "Switch",
        "aa",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=3),
    )
    port_map = build_port_map([gateway, switch])
    assert port_map[(normalize_mac("bb"), normalize_mac("aa"))] == "Port 3"


def test_build_port_map_only_unifi_false():
    switch = make_device(
        "Switch",
        "aa",
        lldp_info=[LLDPEntry("cc:dd:ee:ff:00:11", "Port 1", local_port_idx=1)],
    )
    port_map = build_port_map([switch], only_unifi=False)
    assert (normalize_mac("aa"), "cc:dd:ee:ff:00:11") in port_map


def test_build_edges_trunk_detection():
    switch_a = make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[make_port(1, native_vlan=1, tagged_vlans=(10, 20))],
    )
    switch_b = make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is True
    assert edges[0].vlans == (1, 10, 20)


def test_build_edges_single_vlan_not_trunk():
    switch_a = make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[make_port(1, native_vlan=10)],
    )
    switch_b = make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is False
    assert edges[0].vlans == (10,)


def test_build_edges_with_non_unifi_neighbor_rank():
    switch = make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("cc:dd:ee:ff:00:11", "Port 1")],
    )
    assert len(build_edges([switch], only_unifi=False, include_ports=True)) == 1


def test_build_edges_speed_from_reverse_direction():
    switch_b = make_device(
        "Switch B",
        "aa:bb:cc:dd:ee:02",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:01", "eth1", local_port_idx=1)],
        port_table=[make_port(1, speed=2500)],
    )
    switch_a = make_device("Switch A", "aa:bb:cc:dd:ee:01")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].speed == 2500
