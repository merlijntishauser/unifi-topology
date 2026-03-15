"""Tests for uplink-link building behavior."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import _maybe_add_uplink_link, build_edges
from unifi_topology.model.topology import UplinkInfo


def test_maybe_add_uplink_link_adds_new():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        make_device("Switch", "aa"),
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
        make_device("Switch", "aa"),
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
        make_device("Switch", "aa"),
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
        make_device("Switch", "aa"),
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
        make_device("Switch", "aa"),
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
