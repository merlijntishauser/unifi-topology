"""Tests for edge port VLAN and map population helpers."""

from __future__ import annotations

from tests.edge_port_helpers import make_port
from unifi_topology.model._edge_ports import _populate_port_maps, _port_vlans_by_idx


def test_port_vlans_by_idx_native_vlan():
    assert _port_vlans_by_idx([make_port(1, native_vlan=10)], 1) == (10,)


def test_port_vlans_by_idx_tagged_vlans():
    assert _port_vlans_by_idx([make_port(1, tagged_vlans=(20, 30))], 1) == (20, 30)


def test_port_vlans_by_idx_native_and_tagged():
    ports = [make_port(1, native_vlan=10, tagged_vlans=(20, 30))]
    assert _port_vlans_by_idx(ports, 1) == (10, 20, 30)


def test_port_vlans_by_idx_deduplicates():
    ports = [make_port(1, native_vlan=20, tagged_vlans=(20, 30))]
    assert _port_vlans_by_idx(ports, 1) == (20, 30)


def test_port_vlans_by_idx_no_vlans():
    assert _port_vlans_by_idx([make_port(1)], 1) == ()


def test_port_vlans_by_idx_port_not_found():
    assert _port_vlans_by_idx([make_port(1)], 99) == ()


def test_populate_port_maps_poe():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps("A", "B", 1, {1: True}, [make_port(1)], poe_map, speed_map, vlan_map)
    assert poe_map[("A", "B")] is True


def test_populate_port_maps_speed():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps(
        "A",
        "B",
        1,
        {},
        [make_port(1, speed=1000)],
        poe_map,
        speed_map,
        vlan_map,
    )
    assert speed_map[("A", "B")] == 1000


def test_populate_port_maps_vlans():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps(
        "A",
        "B",
        1,
        {},
        [make_port(1, native_vlan=10, tagged_vlans=(20, 30))],
        poe_map,
        speed_map,
        vlan_map,
    )
    assert vlan_map[("A", "B")] == (10, 20, 30)


def test_populate_port_maps_no_poe_no_speed_no_vlans():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps("A", "B", 1, {}, [make_port(1)], poe_map, speed_map, vlan_map)
    assert ("A", "B") not in poe_map
    assert ("A", "B") not in speed_map
    assert ("A", "B") not in vlan_map
