"""Private helpers for device-to-device edge discovery."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from ._edge_ports import (
    _populate_port_maps,
    _resolve_port_idx_from_lldp,
)
from .helpers import normalize_mac
from .lldp import LLDPEntry, local_port_label
from .topology import Device, PoeMap, PortMap, SpeedMap, UplinkInfo, VlanMap
from .topology import (
    build_device_index as _build_device_index,
)


def _uplink_name(
    uplink: UplinkInfo | None,
    index: dict[str, str],
    *,
    only_unifi: bool,
) -> str | None:
    """Get upstream device name from uplink info."""
    if not uplink:
        return None
    resolved = _uplink_name_by_mac(uplink, index)
    if resolved is not None:
        return resolved
    return _uplink_name_fallback(uplink, only_unifi=only_unifi)


def _uplink_name_by_mac(uplink: UplinkInfo, index: dict[str, str]) -> str | None:
    if not uplink.mac:
        return None
    return index.get(normalize_mac(uplink.mac))


def _uplink_name_fallback(uplink: UplinkInfo, *, only_unifi: bool) -> str | None:
    if uplink.name:
        return uplink.name
    if not only_unifi and uplink.mac:
        return uplink.mac
    return None


def _maybe_add_uplink_link(
    device: Device,
    upstream_name: str,
    *,
    uplink: UplinkInfo | None,
    port_map: PortMap,
    raw_links: list[tuple[str, str]],
    seen: set[frozenset[str]],
    include_ports: bool,
) -> None:
    """Add uplink-based edge if not already seen."""
    key = frozenset({device.name, upstream_name})
    if key in seen:
        return
    if uplink and uplink.port is not None and include_ports:
        port_map[(upstream_name, device.name)] = f"Port {uplink.port}"
    raw_links.append((upstream_name, device.name))
    seen.add(key)


@dataclass(frozen=True)
class EdgeInputs:
    """Normalized device inputs for edge discovery."""

    devices: list[Device]
    index: dict[str, str]
    device_by_name: dict[str, Device]


@dataclass
class EdgeDiscoveryResult:
    """Mutable edge discovery state collected from device data."""

    raw_links: list[tuple[str, str]] = field(default_factory=list)
    port_map: PortMap = field(default_factory=dict)
    poe_map: PoeMap = field(default_factory=dict)
    speed_map: SpeedMap = field(default_factory=dict)
    vlan_map: VlanMap = field(default_factory=dict)
    seen: set[frozenset[str]] = field(default_factory=set)


def prepare_edge_inputs(devices: Iterable[Device]) -> EdgeInputs:
    """Sort devices and build lookup maps used by edge discovery."""
    ordered_devices = sorted(devices, key=lambda item: (item.name.lower(), item.mac.lower()))
    return EdgeInputs(
        devices=ordered_devices,
        index=_build_device_index(ordered_devices),
        device_by_name={device.name: device for device in ordered_devices},
    )


def _sorted_lldp_entries(device: Device) -> list[LLDPEntry]:
    return sorted(
        device.lldp_info,
        key=lambda item: (
            normalize_mac(item.chassis_id),
            str(item.port_id or ""),
            str(item.port_desc or ""),
        ),
    )


def _lldp_peer_name(
    lldp_entry: LLDPEntry,
    index: dict[str, str],
    *,
    only_unifi: bool,
) -> str | None:
    peer_mac = normalize_mac(lldp_entry.chassis_id)
    peer_name = index.get(peer_mac)
    if peer_name is not None:
        return peer_name
    if only_unifi:
        return None
    return lldp_entry.chassis_id


def _lldp_label_entry(lldp_entry: LLDPEntry, resolved_port_idx: int | None) -> LLDPEntry:
    if resolved_port_idx is None:
        return lldp_entry
    return LLDPEntry(
        chassis_id=lldp_entry.chassis_id,
        port_id=lldp_entry.port_id,
        port_desc=lldp_entry.port_desc,
        local_port_name=lldp_entry.local_port_name,
        local_port_idx=resolved_port_idx,
    )


def _record_link(
    left_name: str,
    right_name: str,
    raw_links: list[tuple[str, str]],
    seen: set[frozenset[str]],
) -> bool:
    key = frozenset({left_name, right_name})
    if key in seen:
        return False
    raw_links.append((left_name, right_name))
    seen.add(key)
    return True


def _add_lldp_port_details(
    device: Device,
    peer_name: str,
    lldp_entry: LLDPEntry,
    result: EdgeDiscoveryResult,
) -> None:
    resolved_port_idx = _resolve_port_idx_from_lldp(lldp_entry, device.port_table)
    label = local_port_label(_lldp_label_entry(lldp_entry, resolved_port_idx))
    if label:
        result.port_map[(device.name, peer_name)] = label
    if resolved_port_idx is None:
        return
    _populate_port_maps(
        device.name,
        peer_name,
        resolved_port_idx,
        device.poe_ports,
        device.port_table,
        result.poe_map,
        result.speed_map,
        result.vlan_map,
    )


def _collect_device_lldp_links(
    device: Device,
    index: dict[str, str],
    result: EdgeDiscoveryResult,
    *,
    only_unifi: bool,
) -> bool:
    has_link = False
    for lldp_entry in _sorted_lldp_entries(device):
        peer_name = _lldp_peer_name(lldp_entry, index, only_unifi=only_unifi)
        if peer_name is None:
            continue
        _add_lldp_port_details(device, peer_name, lldp_entry, result)
        has_link = _record_link(device.name, peer_name, result.raw_links, result.seen) or has_link
    return has_link


def _collect_lldp_links(
    devices: list[Device],
    index: dict[str, str],
    port_map: PortMap,
    poe_map: PoeMap,
    speed_map: SpeedMap,
    vlan_map: VlanMap,
    raw_links: list[tuple[str, str]],
    seen: set[frozenset[str]],
    *,
    only_unifi: bool,
) -> set[str]:
    """Collect edges from LLDP data."""
    result = EdgeDiscoveryResult(
        raw_links=raw_links,
        port_map=port_map,
        poe_map=poe_map,
        speed_map=speed_map,
        vlan_map=vlan_map,
        seen=seen,
    )
    devices_with_lldp_edges: set[str] = set()
    for device in devices:
        if _collect_device_lldp_links(device, index, result, only_unifi=only_unifi):
            devices_with_lldp_edges.add(device.name)
    return devices_with_lldp_edges


def _resolve_uplink_target(
    device: Device,
    index: dict[str, str],
    device_by_name: dict[str, Device],
    *,
    only_unifi: bool,
) -> tuple[UplinkInfo | None, str | None]:
    uplink = device.uplink or device.last_uplink
    upstream_name = _uplink_name(uplink, index, only_unifi=only_unifi)
    if not upstream_name:
        return uplink, None
    if only_unifi and upstream_name not in device_by_name:
        return uplink, None
    return uplink, upstream_name


def _collect_uplink_links(
    devices: list[Device],
    devices_with_lldp_edges: set[str],
    index: dict[str, str],
    device_by_name: dict[str, Device],
    port_map: PortMap,
    raw_links: list[tuple[str, str]],
    seen: set[frozenset[str]],
    *,
    include_ports: bool,
    only_unifi: bool,
) -> None:
    """Collect edges from uplink data (fallback for devices without LLDP)."""
    for device in devices:
        if device.name in devices_with_lldp_edges:
            continue
        uplink, upstream_name = _resolve_uplink_target(
            device,
            index,
            device_by_name,
            only_unifi=only_unifi,
        )
        if not upstream_name:
            continue
        _maybe_add_uplink_link(
            device,
            upstream_name,
            uplink=uplink,
            port_map=port_map,
            raw_links=raw_links,
            seen=seen,
            include_ports=include_ports,
        )


def discover_edge_links(
    inputs: EdgeInputs,
    *,
    include_ports: bool,
    only_unifi: bool,
) -> EdgeDiscoveryResult:
    """Discover raw device links and the metadata needed to render them."""
    result = EdgeDiscoveryResult()
    devices_with_lldp_edges = _collect_lldp_links(
        inputs.devices,
        inputs.index,
        result.port_map,
        result.poe_map,
        result.speed_map,
        result.vlan_map,
        result.raw_links,
        result.seen,
        only_unifi=only_unifi,
    )
    _collect_uplink_links(
        inputs.devices,
        devices_with_lldp_edges,
        inputs.index,
        inputs.device_by_name,
        result.port_map,
        result.raw_links,
        result.seen,
        include_ports=include_ports,
        only_unifi=only_unifi,
    )
    return result
