"""Compatibility-focused topology tests for edge-building paths."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from unifi_topology.model.edges import (
    _port_speed_by_idx,
    _resolve_port_idx_from_lldp,
    _tree_edges_from_parent,
    _uplink_name,
    build_edges,
    build_topology,
    build_tree_edges_by_topology,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Device, Edge, PortInfo, UplinkInfo
from unifi_topology.model.topology_coerce import coerce_device, normalize_devices


class DummyDevice:
    def __init__(self, name, mac, lldp_info, port_table=None):
        self.name = name
        self.mac = mac
        self.lldp_info = lldp_info
        self.port_table = port_table or []
        self.model_name = ""
        self.ip = ""
        self.type = ""


def test_build_edges_deduplicates_links():
    dev_a = DummyDevice("Switch A", "aa:bb:cc:dd:ee:01", [LLDPEntry("aa:bb:cc:dd:ee:02", "1")])
    dev_b = DummyDevice("Switch B", "aa:bb:cc:dd:ee:02", [LLDPEntry("aa:bb:cc:dd:ee:01", "2")])
    edges = build_edges(normalize_devices([dev_a, dev_b]))
    assert len(edges) == 1


def test_build_edges_orders_deterministically():
    dev_a = DummyDevice(
        "Switch Z",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "2")],
    )
    dev_b = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "1")],
    )
    edges = build_edges(normalize_devices([dev_a, dev_b]))
    assert [(edge.left, edge.right) for edge in edges] == [("Switch A", "Switch Z")]


def test_build_edges_includes_ports():
    dev_a = DummyDevice("Switch A", "aa:bb:cc:dd:ee:01", [LLDPEntry("aa:bb:cc:dd:ee:02", "1")])
    dev_b = DummyDevice("Switch B", "aa:bb:cc:dd:ee:02", [LLDPEntry("aa:bb:cc:dd:ee:01", "2")])
    edges = build_edges(normalize_devices([dev_a, dev_b]), include_ports=True)
    assert edges[0].label == "Switch A: 1 <-> Switch B: 2"


def test_build_edges_only_unifi_filters_unknown_neighbors():
    dev_a = DummyDevice("Switch A", "aa:bb:cc:dd:ee:01", [LLDPEntry("aa:bb:cc:dd:ee:ff", "1")])
    assert build_edges(normalize_devices([dev_a]), only_unifi=True) == []


def test_build_edges_includes_unknown_neighbors_when_allowed():
    dev_a = DummyDevice("Switch A", "aa:bb:cc:dd:ee:01", [LLDPEntry("aa:bb:cc:dd:ee:ff", "1")])
    edges = build_edges(normalize_devices([dev_a]), only_unifi=False)
    assert edges[0].right == "aa:bb:cc:dd:ee:ff"


def test_build_edges_hides_mac_port_id():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth0", local_port_name="Port 2")],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "78:45:58:9F:18:38")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]), include_ports=True)
    assert edges[0].label == "Switch A: Port 2 <-> AP One: ?"


def test_build_edges_port_desc_includes_number_and_name():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [
            LLDPEntry(
                "aa:bb:cc:dd:ee:02",
                "eth1",
                port_desc="uplink fiberdream",
                local_port_idx=1,
            )
        ],
        port_table=[{"port_idx": 1, "poe_enable": True}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]), include_ports=True)
    assert edges[0].label == "Switch A: Port 1 (uplink fiberdream) <-> AP One: Port 0"


def test_build_edges_sets_poe_when_active():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[{"port_idx": 1, "poe_enable": True}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]))
    assert edges[0].poe is True


def test_build_edges_sets_poe_with_power():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[{"port_idx": 1, "poe_power": "7.01"}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]))
    assert edges[0].poe is True


def test_build_edges_sets_poe_with_poe_good():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[{"port_idx": 1, "poe_good": True}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]))
    assert edges[0].poe is True


def test_build_edges_sets_poe_with_port_poe():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[{"port_idx": 1, "port_poe": True}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]))
    assert edges[0].poe is True


def test_build_edges_sets_speed_from_port():
    dev_switch = DummyDevice(
        "Switch A",
        "aa:bb:cc:dd:ee:01",
        [LLDPEntry("aa:bb:cc:dd:ee:02", "eth1", local_port_idx=1)],
        port_table=[{"port_idx": 1, "speed": 1000}],
    )
    dev_ap = DummyDevice(
        "AP One",
        "aa:bb:cc:dd:ee:02",
        [LLDPEntry("aa:bb:cc:dd:ee:01", "eth0")],
    )
    edges = build_edges(normalize_devices([dev_switch, dev_ap]))
    assert edges[0].speed == 1000


@pytest.fixture()
def device_with_uplink_no_lldp():
    class MissingLldpWithUplink:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        uplink = {"uplink_mac": "bb", "uplink_device_name": "Gateway", "uplink_remote_port": 1}
        port_table = []

    return MissingLldpWithUplink()


def test_build_edges_uses_uplink_fallback_fixture(device_with_uplink_no_lldp):
    gateway = Device(
        name="Gateway",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="gateway",
        lldp_info=[],
    )
    device = coerce_device(device_with_uplink_no_lldp)
    edges = build_edges([gateway, device], include_ports=True)
    assert edges[0].label == "Gateway: Port 1 <-> Device: ?"


def test_build_tree_edges_returns_empty_without_gateways():
    assert build_tree_edges_by_topology([Edge("A", "B")], gateways=[]) == []


def test_build_edges_uses_uplink_fallback():
    gateway = Device(
        name="Gateway",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="gateway",
        lldp_info=[],
        poe_ports={1: True},
    )
    switch = Device(
        name="Switch",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="switch",
        lldp_info=[],
        uplink=UplinkInfo(mac="aa", name="Gateway", port=1),
    )
    edges = build_edges([gateway, switch], include_ports=True)
    assert edges[0].label == "Gateway: Port 1 <-> Switch: ?"


def test_build_edges_only_unifi_false_uses_chassis_id():
    lldp = SimpleNamespace(chassis_id="bb", local_port_idx=None, port_id="Port 1", port_desc=None)
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[lldp],
        port_table=[],
    )
    edges = build_edges([coerce_device(device)], only_unifi=False)
    assert edges[0].right == "bb"


def test_build_edges_only_unifi_skips_unknown_uplink():
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        uplink_mac="cc",
    )
    assert build_edges([coerce_device(device)], only_unifi=True) == []


def test_build_edges_only_unifi_false_includes_unknown_uplink():
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        uplink_mac="cc",
    )
    edges = build_edges([coerce_device(device)], only_unifi=False)
    assert (edges[0].left, edges[0].right) == ("cc", "Switch")


def test_build_edges_resolves_port_idx_from_ifname():
    lldp = SimpleNamespace(
        chassis_id="bb",
        local_port_idx=None,
        local_port_name="eth1",
        port_id="Port 1",
        port_desc=None,
    )
    device = SimpleNamespace(
        name="Switch A",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[lldp],
        port_table=[{"port_idx": 2, "ifname": "eth1", "poe_enable": True}],
    )
    neighbor = SimpleNamespace(
        name="Switch B",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
    )
    edges = build_edges([coerce_device(device), coerce_device(neighbor)], include_ports=True)
    assert edges[0].label == "Switch A: Port 2 <-> Switch B: ?"


def test_build_tree_edges_no_gateways():
    assert build_tree_edges_by_topology([], []) == []


def test_build_tree_edges_gateway_not_in_adjacency():
    assert build_tree_edges_by_topology([Edge("A", "B")], ["Missing"]) == []


def test_build_topology_returns_edges():
    lldp = SimpleNamespace(chassis_id="bb", local_port_idx=None, port_id="Port 1", port_desc=None)
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[lldp],
        port_table=[],
    )
    result = build_topology(
        [coerce_device(device)], include_ports=False, only_unifi=False, gateways=[]
    )
    assert result.raw_edges


def test_resolve_port_idx_matches_port_name():
    lldp = LLDPEntry(chassis_id="bb", port_id="Port 3", local_port_name="Port 3")
    port_table = [
        PortInfo(
            port_idx=3,
            name="Port 3",
            ifname=None,
            speed=None,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _resolve_port_idx_from_lldp(lldp, port_table) == 3


def test_resolve_port_idx_matches_port_number():
    lldp = LLDPEntry(chassis_id="bb", port_id="Port 9", local_port_name="Port 9")
    port_table = [
        PortInfo(
            port_idx=9,
            name="Uplink",
            ifname=None,
            speed=None,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _resolve_port_idx_from_lldp(lldp, port_table) == 9


def test_uplink_name_prefers_name_over_mac():
    uplink = UplinkInfo(mac="aa", name="Core Switch", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Core Switch"


def test_tree_edges_from_parent_missing_original():
    parent = {"Switch A": "Gateway"}
    assert _tree_edges_from_parent(parent, {}) == [Edge(left="Gateway", right="Switch A")]


def test_port_speed_by_idx_reads_speed():
    ports = [
        PortInfo(
            port_idx=1,
            name=None,
            ifname=None,
            speed=1000,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _port_speed_by_idx(ports, 1) == 1000
