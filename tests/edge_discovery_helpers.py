from __future__ import annotations

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Device, PortInfo, UplinkInfo


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


def make_device(
    name: str,
    mac: str,
    *,
    device_type: str = "switch",
    lldp_info: list[LLDPEntry] | None = None,
    port_table: list[PortInfo] | None = None,
    poe_ports: dict[int, bool] | None = None,
    uplink: UplinkInfo | None = None,
    last_uplink: UplinkInfo | None = None,
) -> Device:
    return Device(
        name=name,
        model_name="",
        model="",
        mac=mac,
        ip="",
        type=device_type,
        lldp_info=lldp_info or [],
        port_table=port_table or [],
        poe_ports=poe_ports or {},
        uplink=uplink,
        last_uplink=last_uplink,
    )
