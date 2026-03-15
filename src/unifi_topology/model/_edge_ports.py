"""Private helpers for resolving device ports during edge discovery."""

from __future__ import annotations

from .lldp import LLDPEntry
from .ports import extract_port_number
from .topology import PoeMap, PortInfo, SpeedMap, VlanMap


def _lldp_candidates(entry: LLDPEntry) -> list[str]:
    """Get candidate port identifiers from LLDP entry."""
    candidates: list[str] = []
    if entry.local_port_name:
        candidates.append(entry.local_port_name)
    if entry.port_id:
        candidates.append(entry.port_id)
    return candidates


def _match_port_by_name(candidates: list[str], port_table: list[PortInfo]) -> int | None:
    """Match port by name/ifname."""
    for candidate in candidates:
        matched = _matching_port_idx(candidate.strip().lower(), port_table)
        if matched is not None:
            return matched
    return None


def _matching_port_idx(normalized: str, port_table: list[PortInfo]) -> int | None:
    for port in port_table:
        if normalized in _port_name_candidates(port):
            return port.port_idx
    return None


def _port_name_candidates(port: PortInfo) -> tuple[str, ...]:
    values = []
    if port.ifname:
        values.append(port.ifname.strip().lower())
    if port.name:
        values.append(port.name.strip().lower())
    return tuple(values)


def _match_port_by_number(candidates: list[str], port_table: list[PortInfo]) -> int | None:
    """Match port by extracted number."""
    for candidate in candidates:
        number = extract_port_number(candidate)
        if number is None:
            continue
        for port in port_table:
            if port.port_idx == number:
                return port.port_idx
    return None


def _resolve_port_idx_from_lldp(lldp_entry: LLDPEntry, port_table: list[PortInfo]) -> int | None:
    """Resolve port index from LLDP entry."""
    if lldp_entry.local_port_idx is not None:
        return lldp_entry.local_port_idx
    candidates = _lldp_candidates(lldp_entry)
    matched = _match_port_by_name(candidates, port_table)
    if matched is not None:
        return matched
    return _match_port_by_number(candidates, port_table)


def _find_port_by_idx(port_table: list[PortInfo], port_idx: int) -> PortInfo | None:
    """Find port entry by index."""
    for port in port_table:
        if port.port_idx == port_idx:
            return port
    return None


def _port_speed_by_idx(port_table: list[PortInfo], port_idx: int) -> int | None:
    """Get port speed by index."""
    port = _find_port_by_idx(port_table, port_idx)
    return port.speed if port else None


def _port_vlans_by_idx(port_table: list[PortInfo], port_idx: int) -> tuple[int, ...]:
    """Get all VLANs configured on a port (native + tagged)."""
    port = _find_port_by_idx(port_table, port_idx)
    if not port:
        return ()
    vlans: list[int] = []
    if port.native_vlan is not None:
        vlans.append(port.native_vlan)
    vlans.extend(port.tagged_vlans)
    return tuple(sorted(set(vlans)))


def _populate_port_maps(
    device_name: str,
    peer_name: str,
    port_idx: int,
    poe_ports: dict[int, bool],
    port_table: list[PortInfo],
    poe_map: PoeMap,
    speed_map: SpeedMap,
    vlan_map: VlanMap,
) -> None:
    """Populate PoE, speed, and VLAN maps for an edge."""
    if port_idx in poe_ports:
        poe_map[(device_name, peer_name)] = poe_ports[port_idx]
    port_speed = _port_speed_by_idx(port_table, port_idx)
    if port_speed is not None:
        speed_map[(device_name, peer_name)] = port_speed
    port_vlans = _port_vlans_by_idx(port_table, port_idx)
    if port_vlans:
        vlan_map[(device_name, peer_name)] = port_vlans
