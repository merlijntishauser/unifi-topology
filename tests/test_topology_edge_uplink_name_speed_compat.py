"""Compatibility tests for edge uplink ID and speed helpers."""

from __future__ import annotations

from unifi_topology.model.edges import _port_speed_by_idx, _uplink_id
from unifi_topology.model.topology import PortInfo, UplinkInfo


def test_uplink_id_returns_none_when_only_unifi_and_not_in_index():
    uplink = UplinkInfo(mac="aa", name="Core Switch", port=None)
    assert _uplink_id(uplink, {}, only_unifi=True) is None


def test_port_speed_by_idx_reads_speed():
    ports = [
        PortInfo(
            port_idx=1,
            name=None,
            ifname=None,
            speed=1000,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _port_speed_by_idx(ports, 1) == 1000
