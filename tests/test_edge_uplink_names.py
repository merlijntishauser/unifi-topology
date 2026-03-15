"""Tests for uplink naming helpers."""

from __future__ import annotations

from unifi_topology.model.edges import _uplink_name
from unifi_topology.model.topology import UplinkInfo


def test_uplink_name_none_uplink():
    assert _uplink_name(None, {}, only_unifi=True) is None


def test_uplink_name_resolves_mac_from_index():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    index = {"aa:bb:cc:dd:ee:ff": "Core Switch"}
    assert _uplink_name(uplink, index, only_unifi=True) == "Core Switch"


def test_uplink_name_falls_back_to_name_when_mac_not_in_index():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Upstream", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Upstream"


def test_uplink_name_falls_back_to_name_when_mac_is_none():
    uplink = UplinkInfo(mac=None, name="Upstream", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Upstream"


def test_uplink_name_returns_mac_when_not_only_unifi():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    assert _uplink_name(uplink, {}, only_unifi=False) == "aa:bb:cc:dd:ee:ff"


def test_uplink_name_returns_none_when_only_unifi_and_no_match():
    uplink = UplinkInfo(mac=None, name=None, port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) is None
