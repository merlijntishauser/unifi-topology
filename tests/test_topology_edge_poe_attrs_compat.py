"""Compatibility tests for edge discovery PoE attributes."""

from __future__ import annotations

from tests.topology_edge_helpers import DummyDevice
from unifi_topology.model.edges import build_edges
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology_coerce import normalize_devices


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
