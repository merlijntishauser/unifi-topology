"""Tests for connect_request_ip extraction during device coercion."""

from __future__ import annotations

from unifi_topology.model.topology_coerce import normalize_devices


def _raw_gateway(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Gateway",
        "mac": "aa:bb:cc:dd:ee:ff",
        "model": "UDMPRO",
        "ip": "100.64.1.1",
        "type": "udm",
        "lldp_info": [],
    }
    base.update(overrides)
    return base


def test_connect_request_ip_extracted():
    devices = normalize_devices([_raw_gateway(connect_request_ip="8.8.8.8")])
    assert devices[0].public_ip == "8.8.8.8"


def test_missing_connect_request_ip():
    devices = normalize_devices([_raw_gateway()])
    assert devices[0].public_ip is None


def test_empty_connect_request_ip():
    devices = normalize_devices([_raw_gateway(connect_request_ip="")])
    assert devices[0].public_ip is None


def test_loopback_ip_filtered():
    devices = normalize_devices([_raw_gateway(connect_request_ip="127.0.0.1")])
    assert devices[0].public_ip is None


def test_unspecified_ip_filtered():
    devices = normalize_devices([_raw_gateway(connect_request_ip="0.0.0.0")])
    assert devices[0].public_ip is None


def test_private_ip_filtered():
    devices = normalize_devices([_raw_gateway(connect_request_ip="192.168.1.1")])
    assert devices[0].public_ip is None


def test_link_local_ip_filtered():
    devices = normalize_devices([_raw_gateway(connect_request_ip="169.254.1.1")])
    assert devices[0].public_ip is None


def test_invalid_ip_filtered():
    devices = normalize_devices([_raw_gateway(connect_request_ip="not-an-ip")])
    assert devices[0].public_ip is None
