from __future__ import annotations

from pathlib import Path

import pytest

from tests.contract_helpers import (
    assert_client_contract,
    assert_device_contract,
    load_fixture,
)
from unifi_topology.model.clients import build_client_edges, build_client_port_map
from unifi_topology.model.edges import build_edges
from unifi_topology.model.topology import build_device_index
from unifi_topology.model.topology_coerce import normalize_devices

pytestmark = pytest.mark.contract

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_devices_fixture() -> list[object]:
    return load_fixture(str(FIXTURES_DIR / "unifi_devices.json"), "devices")


def _load_clients_fixture() -> list[object]:
    return load_fixture(str(FIXTURES_DIR / "unifi_clients.json"), "clients")


def test_unifi_device_fixture_contract():
    devices = _load_devices_fixture()
    assert devices
    for device in devices:
        assert_device_contract(device)


def test_unifi_client_fixture_contract():
    clients = _load_clients_fixture()
    assert clients
    for client in clients:
        assert_client_contract(client)


def test_unifi_fixture_normalization_contract():
    devices = _load_devices_fixture()
    normalized = normalize_devices(devices)
    edges = build_edges(normalized, include_ports=True, only_unifi=False)
    assert normalized
    assert edges


def test_unifi_fixture_client_edges_contract():
    devices = normalize_devices(_load_devices_fixture())
    clients = _load_clients_fixture()
    edges = build_client_edges(
        clients,
        build_device_index(devices),
        include_ports=True,
        client_mode="all",
    )
    assert any(edge.label and "Port 5" in edge.label for edge in edges)


def test_unifi_fixture_client_ports_contract():
    devices = normalize_devices(_load_devices_fixture())
    clients = _load_clients_fixture()
    client_ports = build_client_port_map(devices, clients, client_mode="all")
    # Keys are now normalized MACs; "Core Switch" has MAC aa:bb:cc:dd:ee:02
    rows = client_ports.get("aa:bb:cc:dd:ee:02", [])
    # Values are (port, client_mac) tuples; "Desk PC" has MAC aa:bb:cc:dd:ee:10
    assert (5, "aa:bb:cc:dd:ee:10") in rows


def test_fixture_data_round_trip_contract():
    """Contract: device fixtures can be normalized and produce edges."""
    devices = _load_devices_fixture()
    clients = _load_clients_fixture()
    normalized = normalize_devices(devices)
    edges = build_edges(normalized, include_ports=True, only_unifi=False)
    assert normalized
    assert edges
    assert clients
