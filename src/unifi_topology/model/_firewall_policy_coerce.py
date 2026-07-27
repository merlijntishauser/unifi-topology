"""Private helpers for coercing firewall zones, policies, and groups."""

from __future__ import annotations

from collections.abc import Iterable

from . import _firewall_nested
from .firewall import FirewallGroup, FirewallPolicy, FirewallZone
from .helpers import as_bool, as_int, first_attr


def _resolve_action(entry: object) -> str:
    """Extract and normalise the firewall action (defaults to BLOCK)."""
    action = _firewall_nested._as_str(first_attr(entry, "action", "policy_action")).upper()
    return action if action else "BLOCK"


def _policy_tuple_field(
    entry: object,
    *,
    flat_keys: tuple[str, ...],
    nested_resolver,
) -> tuple[str, ...]:
    values = _firewall_nested._as_tuple_str(first_attr(entry, *flat_keys))
    if values:
        return values
    return nested_resolver(entry)


def _build_policy(entry: object, policy_id: str) -> FirewallPolicy:
    """Build a FirewallPolicy from a raw entry with a validated ID."""
    source_zone, dest_zone = _firewall_nested._resolve_zone_ids(entry)
    enabled_raw = first_attr(entry, "enabled")
    return FirewallPolicy(
        id=policy_id,
        name=_firewall_nested._as_str(first_attr(entry, "name", "description", "policy_name")),
        enabled=as_bool(enabled_raw) if enabled_raw is not None else True,
        action=_resolve_action(entry),
        source_zone_id=source_zone,
        destination_zone_id=dest_zone,
        protocol=_firewall_nested._as_str(
            first_attr(entry, "protocol", "ip_protocol"), default="all"
        ),
        port_ranges=_policy_tuple_field(
            entry,
            flat_keys=("port_ranges", "ports", "dst_port"),
            nested_resolver=_firewall_nested._port_ranges_from_nested,
        ),
        ip_ranges=_policy_tuple_field(
            entry,
            flat_keys=("ip_ranges", "addresses", "dst_address"),
            nested_resolver=_firewall_nested._ip_ranges_from_nested,
        ),
        description=_firewall_nested._as_str(first_attr(entry, "description", "desc")),
        index=as_int(first_attr(entry, "index", "rule_index", "order", "position")),
        predefined=as_bool(first_attr(entry, "predefined", "is_predefined")),
        source_ip_ranges=_policy_tuple_field(
            entry,
            flat_keys=("source_ip_ranges", "src_address"),
            nested_resolver=_firewall_nested._source_ip_ranges_from_nested,
        ),
        source_mac_addresses=_firewall_nested._mac_addresses_from_nested(entry, "source"),
        source_port_ranges=_policy_tuple_field(
            entry,
            flat_keys=("source_port_ranges", "src_port"),
            nested_resolver=_firewall_nested._source_port_ranges_from_nested,
        ),
        source_network_id=_firewall_nested._network_id_from_nested(entry, "source"),
        destination_mac_addresses=_firewall_nested._mac_addresses_from_nested(entry, "destination"),
        destination_network_id=_firewall_nested._network_id_from_nested(entry, "destination"),
        source_port_group_id=_firewall_nested._group_id_from_nested(
            entry, "source", "port_group_id"
        ),
        destination_port_group_id=_firewall_nested._group_id_from_nested(
            entry,
            "destination",
            "port_group_id",
        ),
        source_address_group_id=_firewall_nested._group_id_from_nested(
            entry,
            "source",
            "address_group_id",
        ),
        destination_address_group_id=_firewall_nested._group_id_from_nested(
            entry,
            "destination",
            "address_group_id",
        ),
        source_matching_target=_firewall_nested._matching_target_from_nested(entry, "source"),
        destination_matching_target=_firewall_nested._matching_target_from_nested(
            entry, "destination"
        ),
        destination_web_domains=_firewall_nested._web_domains_from_nested(entry),
        destination_web_matching_type=_firewall_nested._web_matching_type_from_nested(entry),
        destination_app_ids=_firewall_nested._app_ids_from_nested(entry),
        connection_state_type=_firewall_nested._as_str(
            first_attr(entry, "connection_state_type", "state_type")
        ),
        connection_logging=as_bool(first_attr(entry, "connection_logging", "logging")),
        schedule=_firewall_nested._as_str(first_attr(entry, "schedule")),
        match_ip_sec=_firewall_nested._as_str(first_attr(entry, "match_ip_sec", "ipsec")),
    )


def normalize_firewall_zones(raw: Iterable[object]) -> list[FirewallZone]:
    """Normalize raw zone data to FirewallZone dataclasses."""
    zones: list[FirewallZone] = []
    for entry in raw:
        zone_id = _firewall_nested._as_str(first_attr(entry, "_id", "id", "zone_id"))
        if not zone_id:
            continue
        zones.append(
            FirewallZone(
                id=zone_id,
                name=_firewall_nested._as_str(first_attr(entry, "name", "zone_name")),
                network_ids=_firewall_nested._as_tuple_str(
                    first_attr(entry, "networkIds", "network_ids", "networks")
                ),
            )
        )
    return zones


def normalize_firewall_policies(raw: Iterable[object]) -> list[FirewallPolicy]:
    """Normalize raw policy data to FirewallPolicy dataclasses."""
    policies: list[FirewallPolicy] = []
    for entry in raw:
        policy_id = _firewall_nested._as_str(first_attr(entry, "_id", "id", "policy_id"))
        if not policy_id:
            continue
        policies.append(_build_policy(entry, policy_id))
    return policies


def normalize_firewall_groups(raw: Iterable[object]) -> list[FirewallGroup]:
    """Normalize raw group data to FirewallGroup dataclasses."""
    groups: list[FirewallGroup] = []
    for entry in raw:
        group_id = _firewall_nested._as_str(first_attr(entry, "_id", "id", "group_id"))
        if not group_id:
            continue
        groups.append(
            FirewallGroup(
                id=group_id,
                name=_firewall_nested._as_str(first_attr(entry, "name", "group_name")),
                group_type=_firewall_nested._as_str(first_attr(entry, "group_type", "type")),
                members=_firewall_nested._as_tuple_str(
                    first_attr(entry, "group_members", "members")
                ),
            )
        )
    return groups
