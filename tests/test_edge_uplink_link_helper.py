"""Tests for uplink-link helper behavior."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model._edge_discovery import _maybe_add_uplink_link
from unifi_topology.model.helpers import normalize_mac
from unifi_topology.model.topology import UplinkInfo


def test_maybe_add_uplink_link_adds_new():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    device = make_device("Switch", "aa")
    _maybe_add_uplink_link(
        device,
        "bb",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    device_mac = normalize_mac("aa")
    assert raw_links == [("bb", device_mac)]
    assert port_map[("bb", device_mac)] == "Port 1"


def test_maybe_add_uplink_link_skips_seen():
    raw_links: list[tuple[str, str]] = []
    device_mac = normalize_mac("aa")
    seen: set[frozenset[str]] = {frozenset({device_mac, "bb"})}
    port_map: dict[tuple[str, str], str] = {}
    _maybe_add_uplink_link(
        make_device("Switch", "aa"),
        "bb",
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
    device = make_device("Switch", "aa")
    _maybe_add_uplink_link(
        device,
        "bb",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=1),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=False,
    )
    device_mac = normalize_mac("aa")
    assert raw_links == [("bb", device_mac)]
    assert ("bb", device_mac) not in port_map


def test_maybe_add_uplink_link_no_uplink_port():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    device = make_device("Switch", "aa")
    _maybe_add_uplink_link(
        device,
        "bb",
        uplink=UplinkInfo(mac="bb", name="Gateway", port=None),
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    device_mac = normalize_mac("aa")
    assert raw_links == [("bb", device_mac)]
    assert ("bb", device_mac) not in port_map


def test_maybe_add_uplink_link_none_uplink():
    raw_links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    port_map: dict[tuple[str, str], str] = {}
    device = make_device("Switch", "aa")
    _maybe_add_uplink_link(
        device,
        "bb",
        uplink=None,
        port_map=port_map,
        raw_links=raw_links,
        seen=seen,
        include_ports=True,
    )
    device_mac = normalize_mac("aa")
    assert raw_links == [("bb", device_mac)]
    assert ("bb", device_mac) not in port_map
