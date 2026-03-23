"""Private helpers for assembling ordered edges."""

from __future__ import annotations

from .classify import classify_device_type
from .labels import compose_port_label, order_edge_names
from .topology import Device, Edge, PoeMap, PortMap, SpeedMap, VlanMap


def _rank_for_id(node_id: str, device_by_id: dict[str, Device]) -> int:
    type_rank = {"gateway": 0, "switch": 1, "ap": 2, "other": 3}
    device = device_by_id.get(node_id)
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
    device_by_id: dict[str, Device],
    *,
    include_ports: bool,
    node_names: dict[str, str] | None = None,
) -> list[Edge]:
    """Build ordered Edge objects from raw links."""
    edges: list[Edge] = []
    for source_id, target_id in raw_links:
        left_id = source_id
        right_id = target_id
        if include_ports:
            left_id, right_id = order_edge_names(
                left_id,
                right_id,
                port_map,
                lambda nid: _rank_for_id(nid, device_by_id),
            )
        vlans = _edge_vlans(left_id, right_id, vlan_map)
        edges.append(
            Edge(
                left=left_id,
                right=right_id,
                label=compose_port_label(left_id, right_id, port_map, node_names=node_names)
                if include_ports
                else None,
                poe=_edge_poe(left_id, right_id, poe_map),
                speed=_edge_speed(left_id, right_id, speed_map),
                vlans=vlans,
                active_vlans=(),
                is_trunk=len(vlans) > 1,
            )
        )
    return edges
