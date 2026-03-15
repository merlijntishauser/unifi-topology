"""Tests for edge discovery and uplink fallback helpers."""

from __future__ import annotations

from unifi_topology.model.edges import (
    _maybe_add_uplink_link,
    _uplink_name,
    build_edges,
    build_port_map,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Device, PortInfo, UplinkInfo


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


def _make_device(
    name: str,
    mac: str,
    *,
    device_type: str = "switch",
    lldp_info: list[LLDPEntry] | None = None,
    port_table: list[PortInfo] | None = None,
    poe_ports: dict[int, bool] | None = None,
    uplink: UplinkInfo | None = None,
    last_uplink: UplinkInfo | None = None,
) -> Device:
    return Device(
        name=name,
        model_name="",
        model="",
        mac=mac,
        ip="",
        type=device_type,
        lldp_info=lldp_info or [],
        port_table=port_table or [],
        poe_ports=poe_ports or {},
        uplink=uplink,
        last_uplink=last_uplink,
    )


def test_uplink_name_none_uplink():
    assert _uplink_name(None, {}, only_unifi=True) is None


def test_uplink_name_resolves_mac_from_index():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    index = {"aa:bb:cc:dd:ee:ff": "Core Switch"}
    assert _uplink_name(uplink, index, only_unifi=True) == "Core Switch"


def test_uplink_name_falls_back_to_name_when_mac_not_in_index():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Upstream", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Upstream"


def test_uplink_name_falls_back_to_name_when_mac_is_none():
    uplink = UplinkInfo(mac=None, name="Upstream", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Upstream"


def test_uplink_name_returns_mac_when_not_only_unifi():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    assert _uplink_name(uplink, {}, only_unifi=False) == "aa:bb:cc:dd:ee:ff"


def test_uplink_name_returns_none_when_only_unifi_and_no_match():
    uplink = UplinkInfo(mac=None, name=None, port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) is None


def test_maybe_add_uplink_link_adds_new():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        _make_device("Switch", "aa"),
        "Gateway",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == [("Gateway", "Switch")]
    assert port_map[("Gateway", "Switch")] == "Port 1"


def test_maybe_add_uplink_link_skips_seen():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = {frozenset({"Switch", "Gateway"})}
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        _make_device("Switch", "aa"),
        "Gateway",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == []


def test_maybe_add_uplink_link_no_port_label_when_not_include_ports():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        _make_device("Switch", "aa"),
        "Gateway",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=False,
    )
    assert raw_links == [("Gateway", "Switch")]
    assert ("Gateway", "Switch") not in port_map


def test_maybe_add_uplink_link_no_uplink_port():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        _make_device("Switch", "aa"),
        "Gateway",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=None),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == [("Gateway", "Switch")]
    assert ("Gateway", "Switch") not in port_map


def test_maybe_add_uplink_link_none_uplink():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        _make_device("Switch", "aa"),
        "Gateway",
        uplink=None,
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == [("Gateway", "Switch")]
    assert ("Gateway", "Switch") not in port_map


def test_build_edges_uplink_only_unifi_skips_unknown_upstream():
    switch = _make_device(
        "Switch",
        "aa",
        uplink=UplinkInfo(mac=None, name="Unknown Device", port=1),
    )
    assert build_edges([switch], only_unifi=True) == []


def test_build_edges_uses_last_uplink_when_uplink_missing():
    gateway = _make_device("Gateway", "bb", device_type="gateway")
    switch = _make_device(
        "Switch",
        "aa",
        last_uplink=UplinkInfo(mac="bb", name="Gateway", port=2),
    )
    edges = build_edges([gateway, switch], include_ports=True)
    assert len(edges) == 1
    assert edges[0].label == "Gateway: Port 2 <-> Switch: ?"


def test_build_edges_lldp_with_vlans():
    switch = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[_make_port(1, native_vlan=10, tagged_vlans=(20, 30))],
    )
    peer = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch, peer])
    assert edges[0].vlans == (10, 20, 30)
    assert edges[0].is_trunk is True


def test_build_port_map_from_lldp():
    switch = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
    )
    peer = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    port_map = build_port_map([switch, peer])
    assert ("Switch A", "Switch B") in port_map


def test_build_port_map_from_uplink():
    gateway = _make_device("Gateway", "bb", device_type="gateway")
    switch = _make_device(
        "Switch",
        "aa",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=3),
    )
    port_map = build_port_map([gateway, switch])
    assert port_map[("Gateway", "Switch")] == "Port 3"


def test_build_port_map_only_unifi_false():
    switch = _make_device(
        "Switch",
        "aa",
        lldp_info=[LLDPEntry("cc:dd:ee:ff:00:11", "Port 1", local_port_idx=1)],
    )
    port_map = build_port_map([switch], only_unifi=False)
    assert ("Switch", "cc:dd:ee:ff:00:11") in port_map


def test_build_edges_trunk_detection():
    switch_a = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[_make_port(1, native_vlan=1, tagged_vlans=(10, 20))],
    )
    switch_b = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is True
    assert edges[0].vlans == (1, 10, 20)


def test_build_edges_single_vlan_not_trunk():
    switch_a = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[_make_port(1, native_vlan=10)],
    )
    switch_b = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is False
    assert edges[0].vlans == (10,)


def test_build_edges_with_non_unifi_neighbor_rank():
    switch = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("cc:dd:ee:ff:00:11", "Port 1")],
    )
    assert len(build_edges([switch], only_unifi=False, include_ports=True)) == 1


def test_build_edges_speed_from_reverse_direction():
    switch_b = _make_device(
        "Switch B",
        "aa:bb:cc:dd:ee:02",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:01", "eth1", local_port_idx=1)],
        port_table=[_make_port(1, speed=2500)],
    )
    switch_a = _make_device("Switch A", "aa:bb:cc:dd:ee:01")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].speed == 2500
