"""Compatibility-focused topology tests for client builder helpers."""

from __future__ import annotations

from unifi_topology.model.clients import (
    build_client_edges,
    build_client_port_map,
    build_node_type_map,
)
from unifi_topology.model.topology import Device


def test_build_client_edges_skips_unwired():
    assert (
        build_client_edges(
            [{"name": "Client", "is_wired": False, "sw_mac": "aa"}], {"aa": "Switch"}
        )
        == []
    )


def test_build_client_edges_include_ports_without_port():
    edges = build_client_edges(
        [{"name": "Client", "is_wired": True, "sw_mac": "aa"}],
        {"aa": "Switch"},
        include_ports=True,
    )
    assert edges[0].label is None


def test_build_node_type_map_skips_unwired_clients():
    assert "Client" not in build_node_type_map([], [{"name": "Client", "is_wired": False}])


def test_build_client_edges_missing_name_or_uplink():
    assert build_client_edges([{"name": "", "is_wired": True}], {"aa": "Switch"}) == []


def test_build_client_edges_dedupes():
    clients = [
        {"name": "Client", "is_wired": True, "sw_mac": "aa"},
        {"name": "Client", "is_wired": True, "sw_mac": "aa"},
    ]
    assert len(build_client_edges(clients, {"aa": "Switch"})) == 1


def test_build_node_type_map_adds_wired_client():
    node_types = build_node_type_map([], [{"name": "Client", "is_wired": True}])
    assert node_types["Client"] == "client"


def test_build_client_port_map_skips_unknown_device():
    devices = [
        Device(name="Switch", model_name="", model="", mac="aa", ip="", type="usw", lldp_info=[])
    ]
    clients = [{"name": "Client", "is_wired": True, "sw_mac": "cc", "sw_port": 3}]
    assert build_client_port_map(devices, clients, client_mode="wired") == {}
