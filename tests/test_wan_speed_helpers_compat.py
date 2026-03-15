"""Compatibility-focused tests for WAN speed helpers."""

from __future__ import annotations

from unifi_topology.model.wan import _normalize_wan_speed


def test_normalize_wan_speed_converts_gbps_to_mbps():
    assert _normalize_wan_speed(10) == 10000
    assert _normalize_wan_speed(1) == 1000
    assert _normalize_wan_speed(100) == 100000
    assert _normalize_wan_speed(25) == 25000


def test_normalize_wan_speed_preserves_mbps():
    assert _normalize_wan_speed(1000) == 1000
    assert _normalize_wan_speed(10000) == 10000
    assert _normalize_wan_speed(100000) == 100000


def test_normalize_wan_speed_handles_none_and_zero():
    assert _normalize_wan_speed(None) is None
    assert _normalize_wan_speed(0) == 0
