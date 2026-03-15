"""Private helpers for assembling ordered edges."""

from __future__ import annotations

from .classify import classify_device_type
from .labels import compose_port_label, order_edge_names
from .topology import Device, Edge, PoeMap, PortMap, SpeedMap, VlanMap


def _rank_for_name(name: str, device_by_name: dict[str, Device]) -> int:
    type_rank = {"gateway": 0, "switch": 1, "ap": 2, "other": 3}
    device = device_by_name.get(name)
    if not device:
        return 3
    return type_rank.get(classify_device_type(device), 3)


def _edge_poe(
    left_name: str,
    right_name: str,
    poe_map: PoeMap,
) -> bool:
    return poe_map.get((left_name, right_name), False) or poe_map.get(
        (right_name, left_name), False
    )


def _edge_speed(
    left_name: str,
    right_name: str,
    speed_map: SpeedMap,
) -> int | None:
    speed = speed_map.get((left_name, right_name))
    if speed is None:
        return speed_map.get((right_name, left_name))
    return speed


def _edge_vlans(
    left_name: str,
    right_name: str,
    vlan_map: VlanMap,
) -> tuple[int, ...]:
    vlans_lr = vlan_map.get((left_name, right_name), ())
    vlans_rl = vlan_map.get((right_name, left_name), ())
    return tuple(sorted(set(vlans_lr) | set(vlans_rl)))


def _build_ordered_edges(
    raw_links: list[tuple[str, str]],
    port_map: PortMap,
    poe_map: PoeMap,
    speed_map: SpeedMap,
    vlan_map: VlanMap,
    device_by_name: dict[str, Device],
    *,
    include_ports: bool,
) -> list[Edge]:
    """Build ordered Edge objects from raw links."""
    edges: list[Edge] = []
    for source_name, target_name in raw_links:
        left_name = source_name
        right_name = target_name
        if include_ports:
            left_name, right_name = order_edge_names(
                left_name,
                right_name,
                port_map,
                lambda name: _rank_for_name(name, device_by_name),
            )
        vlans = _edge_vlans(left_name, right_name, vlan_map)
        edges.append(
            Edge(
                left=left_name,
                right=right_name,
                label=compose_port_label(left_name, right_name, port_map)
                if include_ports
                else None,
                poe=_edge_poe(left_name, right_name, poe_map),
                speed=_edge_speed(left_name, right_name, speed_map),
                vlans=vlans,
                active_vlans=(),
                is_trunk=len(vlans) > 1,
            )
        )
    return edges
