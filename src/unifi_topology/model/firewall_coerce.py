"""Coerce raw UniFi API responses to firewall dataclasses."""

from __future__ import annotations

from collections.abc import Iterable

from .firewall import FirewallGroup, FirewallPolicy, FirewallZone
from .helpers import as_bool, as_int, first_attr


def _as_str(value: object, default: str = "") -> str:
    """Coerce value to string."""
    if value is None:
        return default
    return str(value).strip()


def _as_tuple_str(value: object) -> tuple[str, ...]:
    """Coerce value to tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, list | tuple):
        return tuple(str(v) for v in value if v is not None)
    return ()


def _resolve_action(entry: object) -> str:
    """Extract and normalise the firewall action (defaults to BLOCK)."""
    action = _as_str(first_attr(entry, "action", "policy_action")).upper()
    return action if action else "BLOCK"


def _zone_id_from_nested(entry: object, key: str) -> str:
    """Extract zone_id from a nested dict (e.g. entry["source"]["zone_id"])."""
    nested = first_attr(entry, key)
    if isinstance(nested, dict):
        return _as_str(nested.get("zone_id"))
    return ""


def _resolve_zone_ids(entry: object) -> tuple[str, str]:
    """Extract source and destination zone IDs from a policy entry."""
    source = _as_str(
        first_attr(
            entry,
            "source_zone_id",
            "sourceZoneId",
            "source_zone",
            "src_zone_id",
        )
    ) or _zone_id_from_nested(entry, "source")
    dest = _as_str(
        first_attr(
            entry,
            "destination_zone_id",
            "destinationZoneId",
            "destination_zone",
            "dst_zone_id",
        )
    ) or _zone_id_from_nested(entry, "destination")
    return source, dest


def _port_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract port ranges from nested source/destination dicts."""
    dst = first_attr(entry, "destination")
    if not isinstance(dst, dict):
        return ()
    if dst.get("port_matching_type") == "ANY":
        return ()
    port = dst.get("port")
    if port is not None:
        return (str(port),)
    return ()


def _ip_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract IP ranges from nested destination dict."""
    dst = first_attr(entry, "destination")
    if not isinstance(dst, dict):
        return ()
    ips = dst.get("ips")
    if isinstance(ips, list):
        return tuple(str(ip) for ip in ips if ip is not None)
    return ()


def _build_policy(entry: object, policy_id: str) -> FirewallPolicy:
    """Build a FirewallPolicy from a raw entry with a validated ID."""
    source_zone, dest_zone = _resolve_zone_ids(entry)
    enabled_raw = first_attr(entry, "enabled")
    port_ranges = _as_tuple_str(first_attr(entry, "port_ranges", "ports", "dst_port"))
    if not port_ranges:
        port_ranges = _port_ranges_from_nested(entry)
    ip_ranges = _as_tuple_str(first_attr(entry, "ip_ranges", "addresses", "dst_address"))
    if not ip_ranges:
        ip_ranges = _ip_ranges_from_nested(entry)
    return FirewallPolicy(
        id=policy_id,
        name=_as_str(first_attr(entry, "name", "description", "policy_name")),
        enabled=as_bool(enabled_raw) if enabled_raw is not None else True,
        action=_resolve_action(entry),
        source_zone_id=source_zone,
        destination_zone_id=dest_zone,
        protocol=_as_str(first_attr(entry, "protocol", "ip_protocol"), default="all"),
        port_ranges=port_ranges,
        ip_ranges=ip_ranges,
        description=_as_str(first_attr(entry, "description", "desc")),
        index=as_int(first_attr(entry, "index", "rule_index", "order", "position")),
        predefined=as_bool(first_attr(entry, "predefined", "is_predefined")),
    )


def normalize_firewall_zones(raw: Iterable[object]) -> list[FirewallZone]:
    """Normalize raw zone data to FirewallZone dataclasses."""
    zones: list[FirewallZone] = []
    for entry in raw:
        zone_id = _as_str(first_attr(entry, "_id", "id", "zone_id"))
        if not zone_id:
            continue
        zones.append(
            FirewallZone(
                id=zone_id,
                name=_as_str(first_attr(entry, "name", "zone_name")),
                network_ids=_as_tuple_str(
                    first_attr(entry, "networkIds", "network_ids", "networks")
                ),
            )
        )
    return zones


def normalize_firewall_policies(raw: Iterable[object]) -> list[FirewallPolicy]:
    """Normalize raw policy data to FirewallPolicy dataclasses."""
    policies: list[FirewallPolicy] = []
    for entry in raw:
        policy_id = _as_str(first_attr(entry, "_id", "id", "policy_id"))
        if not policy_id:
            continue
        policies.append(_build_policy(entry, policy_id))
    return policies


def normalize_firewall_groups(raw: Iterable[object]) -> list[FirewallGroup]:
    """Normalize raw group data to FirewallGroup dataclasses."""
    groups: list[FirewallGroup] = []
    for entry in raw:
        group_id = _as_str(first_attr(entry, "_id", "id", "group_id"))
        if not group_id:
            continue
        groups.append(
            FirewallGroup(
                id=group_id,
                name=_as_str(first_attr(entry, "name", "group_name")),
                group_type=_as_str(first_attr(entry, "group_type", "type")),
                members=_as_tuple_str(first_attr(entry, "group_members", "members")),
            )
        )
    return groups
