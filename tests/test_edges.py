"""Tests for unifi_topology.model.edges module."""

from __future__ import annotations

from unifi_topology.model.edges import (
    _lldp_candidates,
    _match_port_by_name,
    _match_port_by_number,
    _maybe_add_uplink_link,
    _populate_port_maps,
    _port_vlans_by_idx,
    _primary_vlan_for_node,
    _uplink_name,
    build_edges,
    build_port_map,
    build_topology,
    build_tree_edges_by_topology,
    enrich_edges_with_active_vlans,
    group_devices_by_type,
    group_nodes_by_vlan,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Device, Edge, PortInfo, UplinkInfo


def _make_port(
    port_idx: int,
    *,
    name: str | None = None,
    ifname: str | None = None,
    speed: int | None = None,
    native_vlan: int | None = None,
    tagged_vlans: tuple[int, ...] = (),
) -> PortInfo:
    """Helper to create a PortInfo with sensible defaults."""
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
    """Helper to create a Device with sensible defaults."""
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


# --- _lldp_candidates ---


def test_lldp_candidates_both_fields():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name="eth0")
    result = _lldp_candidates(entry)
    assert result == ["eth0", "Port 1"]


def test_lldp_candidates_only_local_port_name():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name="eth0")
    result = _lldp_candidates(entry)
    assert result == ["eth0"]


def test_lldp_candidates_only_port_id():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name=None)
    result = _lldp_candidates(entry)
    assert result == ["Port 1"]


def test_lldp_candidates_neither_field():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name=None)
    result = _lldp_candidates(entry)
    assert result == []


# --- _match_port_by_name ---


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


# --- _match_port_by_number ---


def test_match_port_by_number_matches():
    ports = [_make_port(5), _make_port(9)]
    assert _match_port_by_number(["Port 9"], ports) == 9


def test_match_port_by_number_no_port_match():
    ports = [_make_port(1), _make_port(2)]
    assert _match_port_by_number(["Port 9"], ports) is None


def test_match_port_by_number_no_extractable_number():
    ports = [_make_port(1)]
    assert _match_port_by_number(["wan"], ports) is None


# --- _port_vlans_by_idx ---


def test_port_vlans_by_idx_native_vlan():
    ports = [_make_port(1, native_vlan=10)]
    assert _port_vlans_by_idx(ports, 1) == (10,)


def test_port_vlans_by_idx_tagged_vlans():
    ports = [_make_port(1, tagged_vlans=(20, 30))]
    assert _port_vlans_by_idx(ports, 1) == (20, 30)


def test_port_vlans_by_idx_native_and_tagged():
    ports = [_make_port(1, native_vlan=10, tagged_vlans=(20, 30))]
    result = _port_vlans_by_idx(ports, 1)
    assert result == (10, 20, 30)


def test_port_vlans_by_idx_deduplicates():
    ports = [_make_port(1, native_vlan=20, tagged_vlans=(20, 30))]
    result = _port_vlans_by_idx(ports, 1)
    assert result == (20, 30)


def test_port_vlans_by_idx_no_vlans():
    ports = [_make_port(1)]
    assert _port_vlans_by_idx(ports, 1) == ()


def test_port_vlans_by_idx_port_not_found():
    ports = [_make_port(1)]
    assert _port_vlans_by_idx(ports, 99) == ()


# --- _populate_port_maps ---


def test_populate_port_maps_poe():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    ports = [_make_port(1)]
    _populate_port_maps("A", "B", 1, {1: True}, ports, poe_map, speed_map, vlan_map)
    assert poe_map[("A", "B")] is True


def test_populate_port_maps_speed():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    ports = [_make_port(1, speed=1000)]
    _populate_port_maps("A", "B", 1, {}, ports, poe_map, speed_map, vlan_map)
    assert speed_map[("A", "B")] == 1000


def test_populate_port_maps_vlans():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    ports = [_make_port(1, native_vlan=10, tagged_vlans=(20, 30))]
    _populate_port_maps("A", "B", 1, {}, ports, poe_map, speed_map, vlan_map)
    assert vlan_map[("A", "B")] == (10, 20, 30)


def test_populate_port_maps_no_poe_no_speed_no_vlans():
    poe_map: dict[tuple[str, str], bool] = {}
    speed_map: dict[tuple[str, str], int] = {}
    vlan_map: dict[tuple[str, str], tuple[int, ...]] = {}
    ports = [_make_port(1)]
    _populate_port_maps("A", "B", 1, {}, ports, poe_map, speed_map, vlan_map)
    assert ("A", "B") not in poe_map
    assert ("A", "B") not in speed_map
    assert ("A", "B") not in vlan_map


# --- _uplink_name ---


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


# --- _maybe_add_uplink_link ---


def test_maybe_add_uplink_link_adds_new():
    device = _make_device("Switch", "aa")
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        device,
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
    device = _make_device("Switch", "aa")
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = {frozenset({"Switch", "Gateway"})}
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        device,
        "Gateway",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == []


def test_maybe_add_uplink_link_no_port_label_when_not_include_ports():
    device = _make_device("Switch", "aa")
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        device,
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
    device = _make_device("Switch", "aa")
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        device,
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
    device = _make_device("Switch", "aa")
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        device,
        "Gateway",
        uplink=None,
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    assert raw_links == [("Gateway", "Switch")]
    assert ("Gateway", "Switch") not in port_map


# --- build_edges with uplink fallback ---


def test_build_edges_uplink_only_unifi_skips_unknown_upstream():
    """When only_unifi=True, uplink to unknown device should be skipped."""
    switch = _make_device(
        "Switch",
        "aa",
        uplink=UplinkInfo(mac=None, name="Unknown Device", port=1),
    )
    edges = build_edges([switch], only_unifi=True)
    assert edges == []


def test_build_edges_uses_last_uplink_when_uplink_missing():
    """Device with no uplink but last_uplink should use last_uplink."""
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
    """LLDP edges should populate VLAN information from port table."""
    port = _make_port(1, native_vlan=10, tagged_vlans=(20, 30))
    switch = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[port],
    )
    peer = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch, peer])
    assert edges[0].vlans == (10, 20, 30)
    assert edges[0].is_trunk is True


# --- build_port_map ---


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


# --- build_tree_edges_by_topology ---


def test_build_tree_edges_simple_chain():
    edges = [Edge("Gateway", "Switch"), Edge("Switch", "AP")]
    result = build_tree_edges_by_topology(edges, ["Gateway"])
    assert len(result) == 2
    left_right = [(e.left, e.right) for e in result]
    assert ("Gateway", "Switch") in left_right
    assert ("Switch", "AP") in left_right


def test_build_tree_edges_preserves_edge_properties():
    edges = [
        Edge(
            "Gateway",
            "Switch",
            label="Port 1 <-> Port 2",
            poe=True,
            speed=1000,
            vlans=(10, 20),
            is_trunk=True,
        )
    ]
    result = build_tree_edges_by_topology(edges, ["Gateway"])
    assert len(result) == 1
    assert result[0].left == "Gateway"
    assert result[0].right == "Switch"
    assert result[0].label == "Port 1 <-> Port 2"
    assert result[0].poe is True
    assert result[0].speed == 1000
    assert result[0].vlans == (10, 20)
    assert result[0].is_trunk is True


def test_build_tree_edges_gateway_not_in_edges():
    edges = [Edge("A", "B")]
    result = build_tree_edges_by_topology(edges, ["Missing"])
    assert result == []


def test_build_tree_edges_multiple_gateways():
    edges = [Edge("GW1", "Switch"), Edge("GW2", "AP")]
    result = build_tree_edges_by_topology(edges, ["GW1", "GW2"])
    assert len(result) == 2


# --- enrich_edges_with_active_vlans ---


def test_enrich_edges_with_active_vlans_basic():
    edges = [Edge("Switch", "AP", vlans=(10, 20, 30))]
    client_edges = [
        Edge("Switch", "Client1", active_vlans=(10,)),
        Edge("AP", "Client2", active_vlans=(20,)),
    ]
    result = enrich_edges_with_active_vlans(edges, client_edges)
    assert len(result) == 1
    assert result[0].active_vlans == (10, 20)


def test_enrich_edges_with_active_vlans_no_overlap():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    client_edges = [Edge("Switch", "Client1", active_vlans=(99,))]
    result = enrich_edges_with_active_vlans(edges, client_edges)
    assert result[0].active_vlans == ()


def test_enrich_edges_with_active_vlans_empty_clients():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    result = enrich_edges_with_active_vlans(edges, [])
    assert result[0].active_vlans == ()


def test_enrich_edges_preserves_other_fields():
    edges = [
        Edge(
            "Switch",
            "AP",
            label="Port 1",
            poe=True,
            wireless=True,
            speed=1000,
            channel=36,
            vlans=(10,),
            is_trunk=False,
        )
    ]
    client_edges = [Edge("Switch", "Client1", active_vlans=(10,))]
    result = enrich_edges_with_active_vlans(edges, client_edges)
    assert result[0].label == "Port 1"
    assert result[0].poe is True
    assert result[0].wireless is True
    assert result[0].speed == 1000
    assert result[0].channel == 36
    assert result[0].is_trunk is False
    assert result[0].active_vlans == (10,)


# --- group_devices_by_type ---


def test_group_devices_by_type_all_types():
    gw = _make_device("GW", "aa", device_type="gateway")
    sw = _make_device("SW", "bb", device_type="usw")
    ap = _make_device("AP", "cc", device_type="uap")
    other = _make_device("Cam", "dd", device_type="camera")
    groups = group_devices_by_type([gw, sw, ap, other])
    assert "GW" in groups["gateway"]
    assert "SW" in groups["switch"]
    assert "AP" in groups["ap"]
    assert "Cam" in groups["other"]


def test_group_devices_by_type_empty():
    groups = group_devices_by_type([])
    assert groups == {"gateway": [], "switch": [], "ap": [], "other": []}


# --- _primary_vlan_for_node ---


def test_primary_vlan_for_node_uses_active_vlans():
    edges = [Edge("A", "B", active_vlans=(10, 20), vlans=(10, 20, 30))]
    assert _primary_vlan_for_node("A", edges) == 10


def test_primary_vlan_for_node_falls_back_to_vlans():
    edges = [Edge("A", "B", vlans=(30, 40))]
    assert _primary_vlan_for_node("A", edges) == 30


def test_primary_vlan_for_node_no_match():
    edges = [Edge("A", "B")]
    assert _primary_vlan_for_node("C", edges) is None


def test_primary_vlan_for_node_no_vlans():
    edges = [Edge("A", "B")]
    assert _primary_vlan_for_node("A", edges) is None


def test_primary_vlan_for_node_right_side():
    edges = [Edge("A", "B", vlans=(50,))]
    assert _primary_vlan_for_node("B", edges) == 50


# --- group_nodes_by_vlan ---


def test_group_nodes_by_vlan_basic():
    edges = [
        Edge("A", "B", vlans=(10,), active_vlans=(10,)),
        Edge("B", "C", vlans=(20,), active_vlans=(20,)),
    ]
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    assert len(groups) > 0
    assert len(order) > 0
    # All nodes should be accounted for
    all_nodes = set()
    for node_list in groups.values():
        all_nodes.update(node_list)
    assert {"A", "B", "C"} == all_nodes


def test_group_nodes_by_vlan_with_names():
    edges = [Edge("A", "B", vlans=(10,), active_vlans=(10,))]
    groups, order, vlan_ids = group_nodes_by_vlan(edges, vlan_names={10: "Management"})
    assert "Management" in groups
    assert vlan_ids["Management"] == 10


def test_group_nodes_by_vlan_unassigned():
    edges = [Edge("A", "B")]  # no vlans
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    assert "Unassigned" in groups
    assert "A" in groups["Unassigned"]
    assert "B" in groups["Unassigned"]
    assert order[-1] == "Unassigned"


def test_group_nodes_by_vlan_default_name():
    edges = [Edge("A", "B", vlans=(42,), active_vlans=(42,))]
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    assert "VLAN 42" in groups
    assert vlan_ids["VLAN 42"] == 42


def test_group_nodes_by_vlan_mixed():
    """Nodes with and without VLANs should be grouped separately."""
    edges = [
        Edge("A", "B", vlans=(10,), active_vlans=(10,)),
        Edge("C", "D"),  # unassigned
    ]
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    assert "Unassigned" in groups
    assert "C" in groups["Unassigned"]
    assert "D" in groups["Unassigned"]


def test_group_nodes_by_vlan_order():
    """VLAN groups should be ordered by VLAN ID, with Unassigned last."""
    edges = [
        Edge("A", "B", vlans=(20,), active_vlans=(20,)),
        Edge("C", "D", vlans=(10,), active_vlans=(10,)),
        Edge("E", "F"),  # unassigned
    ]
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    vlan_order = [o for o in order if o != "Unassigned"]
    # The VLAN with ID 10 should come before VLAN with ID 20
    assert vlan_ids[vlan_order[0]] < vlan_ids[vlan_order[1]]
    assert order[-1] == "Unassigned"


def test_group_nodes_by_vlan_empty_edges():
    groups, order, vlan_ids = group_nodes_by_vlan([])
    assert groups == {}
    assert order == []
    assert vlan_ids == {}


# --- build_topology ---


def test_build_topology_with_gateways():
    gateway = _make_device("Gateway", "aa", device_type="gateway")
    switch = _make_device(
        "Switch",
        "bb",
        lldp_info=[LLDPEntry("aa", "Port 1")],
    )
    result = build_topology(
        [gateway, switch],
        include_ports=True,
        only_unifi=True,
        gateways=["Gateway"],
    )
    assert len(result.raw_edges) == 1
    assert len(result.tree_edges) == 1


def test_build_topology_without_gateways():
    gateway = _make_device("Gateway", "aa", device_type="gateway")
    switch = _make_device(
        "Switch",
        "bb",
        lldp_info=[LLDPEntry("aa", "Port 1")],
    )
    result = build_topology(
        [gateway, switch],
        include_ports=False,
        only_unifi=True,
        gateways=[],
    )
    assert len(result.raw_edges) == 1
    assert result.tree_edges == []


# --- Edge building with VLAN trunk detection ---


def test_build_edges_trunk_detection():
    """Multiple VLANs on a port should set is_trunk=True."""
    port = _make_port(1, native_vlan=1, tagged_vlans=(10, 20))
    switch_a = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[port],
    )
    switch_b = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is True
    assert edges[0].vlans == (1, 10, 20)


def test_build_edges_single_vlan_not_trunk():
    """Single VLAN on a port should set is_trunk=False."""
    port = _make_port(1, native_vlan=10)
    switch_a = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[port],
    )
    switch_b = _make_device("Switch B", "aa:bb:cc:dd:ee:02")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].is_trunk is False
    assert edges[0].vlans == (10,)


# --- _build_ordered_edges with unknown device rank ---


def test_build_edges_with_non_unifi_neighbor_rank():
    """Non-UniFi neighbors (not in device_by_name) should get rank 3 (other)."""
    switch = _make_device(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        lldp_info=[LLDPEntry("cc:dd:ee:ff:00:11", "Port 1")],
    )
    edges = build_edges([switch], only_unifi=False, include_ports=True)
    assert len(edges) == 1


# --- Speed lookup from both directions ---


def test_build_edges_speed_from_reverse_direction():
    """Speed should be found even when stored under the reverse direction."""
    port = _make_port(1, speed=2500)
    switch_b = _make_device(
        "Switch B",
        "aa:bb:cc:dd:ee:02",
        lldp_info=[LLDPEntry("aa:bb:cc:dd:ee:01", "eth1", local_port_idx=1)],
        port_table=[port],
    )
    switch_a = _make_device("Switch A", "aa:bb:cc:dd:ee:01")
    edges = build_edges([switch_a, switch_b])
    assert edges[0].speed == 2500
