"""Compatibility tests for basic edge discovery behavior."""

from __future__ import annotations

from tests.topology_edge_helpers import DummyDevice
from unifi_topology.model.edges import build_edges
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology_coerce import normalize_devices


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
