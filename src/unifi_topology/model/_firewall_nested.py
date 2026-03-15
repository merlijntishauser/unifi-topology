"""Private helpers for extracting nested firewall policy values."""

from __future__ import annotations

from .helpers import first_attr


def _as_str(value: object, default: str = "") -> str:
    """Coerce value to string."""
    if value is None:
        return default
    return str(value).strip()


def _sequence_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value if item is not None)


def _as_tuple_str(value: object) -> tuple[str, ...]:
    """Coerce value to tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    return _sequence_strings(value)


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


def _nested_mapping(entry: object, key: str) -> dict[object, object] | None:
    nested = first_attr(entry, key)
    if isinstance(nested, dict):
        return nested
    return None


def _port_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract port ranges from nested source/destination dicts."""
    dst = _nested_mapping(entry, "destination")
    if not dst or dst.get("port_matching_type") == "ANY":
        return ()
    port = dst.get("port")
    return (str(port),) if port is not None else ()


def _ip_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract IP ranges from nested destination dict."""
    dst = _nested_mapping(entry, "destination")
    if not dst:
        return ()
    return _sequence_strings(dst.get("ips"))


def _source_ip_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract IP ranges from nested source dict."""
    src = _nested_mapping(entry, "source")
    if not src:
        return ()
    return _sequence_strings(src.get("ips"))


def _source_port_ranges_from_nested(entry: object) -> tuple[str, ...]:
    """Extract port ranges from nested source dict."""
    src = _nested_mapping(entry, "source")
    if not src or src.get("port_matching_type") == "ANY":
        return ()
    port = src.get("port")
    return (str(port),) if port is not None else ()


def _mac_addresses_from_nested(entry: object, key: str) -> tuple[str, ...]:
    """Extract MAC addresses from a nested dict."""
    nested = _nested_mapping(entry, key)
    if not nested:
        return ()
    return _sequence_strings(nested.get("mac_addresses"))


def _network_id_from_nested(entry: object, key: str) -> str:
    """Extract network_id from a nested dict."""
    nested = _nested_mapping(entry, key)
    if nested is None:
        return ""
    network_id = nested.get("network_id")
    return str(network_id) if network_id is not None else ""


def _group_id_from_nested(
    entry: object,
    key: str,
    group_key: str,
) -> str:
    """Extract a firewall group ID from a nested dict."""
    nested = _nested_mapping(entry, key)
    if nested is None:
        return ""
    group_id = nested.get(group_key)
    return str(group_id) if group_id is not None else ""
