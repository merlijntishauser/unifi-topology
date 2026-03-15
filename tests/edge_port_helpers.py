"""Shared helpers for edge port tests."""

from __future__ import annotations

from unifi_topology.model.topology import PortInfo


def make_port(
    port_idx: int,
    *,
    name: str | None = None,
    ifname: str | None = None,
    speed: int | None = None,
    native_vlan: int | None = None,
    tagged_vlans: tuple[int, ...] = (),
) -> PortInfo:
    return PortInfo(
        port_idx=port_idx,
        name=name,
        ifname=ifname,
        speed=speed,
        aggregation_group=None,
        port_poe=False,
        poe_enable=False,
        poe_good=False,
        poe_power=None,
        native_vlan=native_vlan,
        tagged_vlans=tagged_vlans,
    )
