"""Tests for edge port-resolution helpers."""

from __future__ import annotations

from unifi_topology.model.edges import (
    _lldp_candidates,
    _match_port_by_name,
    _match_port_by_number,
    _populate_port_maps,
    _port_vlans_by_idx,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import PortInfo


def _make_port(
    port_idx: int,
    *,
    name: str | None = None,
    ifname: str | None = None,
    speed: int | None = None,
    native_vlan: int | None = None,
    tagged_vlans: tuple[int, ...] = (),
) -> PortInfo:
    return PortInfo(
        port_idx=port_idx,
        name=name,
        ifname=ifname,
        speed=speed,
        aggregation_group=None,
        port_poe=False,
        poe_enable=False,
        poe_good=False,
        poe_power=None,
        native_vlan=native_vlan,
        tagged_vlans=tagged_vlans,
    )


def test_lldp_candidates_both_fields():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name="eth0")
    assert _lldp_candidates(entry) == ["eth0", "Port 1"]


def test_lldp_candidates_only_local_port_name():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name="eth0")
    assert _lldp_candidates(entry) == ["eth0"]


def test_lldp_candidates_only_port_id():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name=None)
    assert _lldp_candidates(entry) == ["Port 1"]


def test_lldp_candidates_neither_field():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name=None)
    assert _lldp_candidates(entry) == []


def test_match_port_by_name_matches_ifname():
    ports = [_make_port(1, ifname="eth0"), _make_port(2, ifname="eth1")]
    assert _match_port_by_name(["eth1"], ports) == 2


def test_match_port_by_name_matches_name():
    ports = [_make_port(3, name="Port 3")]
    assert _match_port_by_name(["Port 3"], ports) == 3


def test_match_port_by_name_case_insensitive():
    ports = [_make_port(1, ifname="ETH0")]
    assert _match_port_by_name(["eth0"], ports) == 1


def test_match_port_by_name_no_match():
    ports = [_make_port(1, ifname="eth0")]
    assert _match_port_by_name(["eth5"], ports) is None


def test_match_port_by_name_empty_candidates():
    ports = [_make_port(1, ifname="eth0")]
    assert _match_port_by_name([], ports) is None


def test_match_port_by_number_matches():
    ports = [_make_port(5), _make_port(9)]
    assert _match_port_by_number(["Port 9"], ports) == 9


def test_match_port_by_number_no_port_match():
    ports = [_make_port(1), _make_port(2)]
    assert _match_port_by_number(["Port 9"], ports) is None


def test_match_port_by_number_no_extractable_number():
    ports = [_make_port(1)]
    assert _match_port_by_number(["wan"], ports) is None


def test_port_vlans_by_idx_native_vlan():
    assert _port_vlans_by_idx([_make_port(1, native_vlan=10)], 1) == (10,)


def test_port_vlans_by_idx_tagged_vlans():
    assert _port_vlans_by_idx([_make_port(1, tagged_vlans=(20, 30))], 1) == (20, 30)


def test_port_vlans_by_idx_native_and_tagged():
    ports = [_make_port(1, native_vlan=10, tagged_vlans=(20, 30))]
    assert _port_vlans_by_idx(ports, 1) == (10, 20, 30)


def test_port_vlans_by_idx_deduplicates():
    ports = [_make_port(1, native_vlan=20, tagged_vlans=(20, 30))]
    assert _port_vlans_by_idx(ports, 1) == (20, 30)


def test_port_vlans_by_idx_no_vlans():
    assert _port_vlans_by_idx([_make_port(1)], 1) == ()


def test_port_vlans_by_idx_port_not_found():
    assert _port_vlans_by_idx([_make_port(1)], 99) == ()


def test_populate_port_maps_poe():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps("A", "B", 1, {1: True}, [_make_port(1)], poe_map, speed_map, vlan_map)
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
        [_make_port(1, speed=1000)],
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
        [_make_port(1, native_vlan=10, tagged_vlans=(20, 30))],
        poe_map,
        speed_map,
        vlan_map,
    )
    assert vlan_map[("A", "B")] == (10, 20, 30)


def test_populate_port_maps_no_poe_no_speed_no_vlans():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    _populate_port_maps("A", "B", 1, {}, [_make_port(1)], poe_map, speed_map, vlan_map)
    assert ("A", "B") not in poe_map
    assert ("A", "B") not in speed_map
    assert ("A", "B") not in vlan_map
