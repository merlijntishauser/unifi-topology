"""Tests for uplink ID helpers."""

from __future__ import annotations

from unifi_topology.model.edges import _uplink_id
from unifi_topology.model.topology import UplinkInfo


def test_uplink_id_none_uplink():
    assert _uplink_id(None, {}, only_unifi=True) is None


def test_uplink_id_resolves_mac_from_index():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    index = {"aa:bb:cc:dd:ee:ff": "Core Switch"}
    assert _uplink_id(uplink, index, only_unifi=True) == "aa:bb:cc:dd:ee:ff"


def test_uplink_id_returns_none_when_mac_not_in_index_and_only_unifi():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Upstream", port=None)
    assert _uplink_id(uplink, {}, only_unifi=True) is None


def test_uplink_id_falls_back_to_name_when_mac_is_none_and_not_only_unifi():
    uplink = UplinkInfo(mac=None, name="Upstream", port=None)
    assert _uplink_id(uplink, {}, only_unifi=False) == "Upstream"


def test_uplink_id_returns_mac_when_not_only_unifi():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name=None, port=None)
    assert _uplink_id(uplink, {}, only_unifi=False) == "aa:bb:cc:dd:ee:ff"


def test_uplink_id_returns_none_when_only_unifi_and_no_match():
    uplink = UplinkInfo(mac=None, name=None, port=None)
    assert _uplink_id(uplink, {}, only_unifi=True) is None
