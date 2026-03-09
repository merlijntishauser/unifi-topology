"""Coerce raw UniFi API responses to firewall dataclasses."""

from __future__ import annotations

from collections.abc import Iterable

from .firewall import FirewallGroup, FirewallPolicy, FirewallZone
from .helpers import first_attr


def _as_str(value: object, default: str = "") -> str:
    """Coerce value to string."""
    if value is None:
        return default
    return str(value).strip()


def _as_bool(value: object, default: bool = False) -> bool:
    """Coerce value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, int):
        return value != 0
    return default


def _as_int(value: object, default: int = 0) -> int:
    """Coerce value to int."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _as_tuple_str(value: object) -> tuple[str, ...]:
    """Coerce value to tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, list | tuple):
        return tuple(str(v) for v in value if v is not None)
    return ()


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

        action = _as_str(first_attr(entry, "action", "policy_action")).upper()
        if not action:
            action = "BLOCK"

        source_zone = _as_str(
            first_attr(
                entry,
                "source_zone_id",
                "sourceZoneId",
                "source_zone",
                "src_zone_id",
            )
        )
        dest_zone = _as_str(
            first_attr(
                entry,
                "destination_zone_id",
                "destinationZoneId",
                "destination_zone",
                "dst_zone_id",
            )
        )

        policies.append(
            FirewallPolicy(
                id=policy_id,
                name=_as_str(first_attr(entry, "name", "description", "policy_name")),
                enabled=_as_bool(first_attr(entry, "enabled"), default=True),
                action=action,
                source_zone_id=source_zone,
                destination_zone_id=dest_zone,
                protocol=_as_str(first_attr(entry, "protocol", "ip_protocol"), default="all"),
                port_ranges=_as_tuple_str(first_attr(entry, "port_ranges", "ports", "dst_port")),
                ip_ranges=_as_tuple_str(first_attr(entry, "ip_ranges", "addresses", "dst_address")),
                description=_as_str(first_attr(entry, "description", "desc")),
                index=_as_int(first_attr(entry, "index", "rule_index", "order", "position")),
                predefined=_as_bool(first_attr(entry, "predefined", "is_predefined")),
            )
        )
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
