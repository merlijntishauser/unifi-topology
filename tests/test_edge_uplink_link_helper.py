"""Tests for uplink-link helper behavior."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import _maybe_add_uplink_link
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
