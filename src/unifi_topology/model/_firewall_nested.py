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
    """Extract MAC addresses from a nested dict.

    Zone-based controllers send these as ``client_macs`` (observed on a 156-policy
    live ruleset); ``mac_addresses`` is kept for older/other payload shapes.
    """
    nested = _nested_mapping(entry, key)
    if not nested:
        return ()
    return _sequence_strings(nested.get("client_macs")) or _sequence_strings(
        nested.get("mac_addresses")
    )


def _matching_target_from_nested(entry: object, key: str) -> str:
    """Extract what a side matches on: ANY, IP, CLIENT, APP, WEB, ...

    This is the general answer to "is this rule restricted?". A rule can be
    narrowed by criteria this model does not parse into a list, but any such rule
    still reports a target other than ``ANY``. An empty string means the payload
    carried no target at all.
    """
    nested = _nested_mapping(entry, key)
    if nested is None:
        return ""
    return _as_str(nested.get("matching_target")).upper()


def _web_domains_from_nested(entry: object) -> tuple[str, ...]:
    """Extract the destination domain allow/block list."""
    dst = _nested_mapping(entry, "destination")
    if not dst:
        return ()
    return _sequence_strings(dst.get("web_domains"))


def _web_matching_type_from_nested(entry: object) -> str:
    """Extract how domains are matched (e.g. CUSTOM for an explicit list)."""
    dst = _nested_mapping(entry, "destination")
    if not dst:
        return ""
    return _as_str(dst.get("web_matching_type")).upper()


def _app_ids_from_nested(entry: object) -> tuple[str, ...]:
    """Extract destination application IDs.

    The controller sends these as integers; they are normalised to strings to
    match every other identifier on the model.
    """
    dst = _nested_mapping(entry, "destination")
    if not dst:
        return ()
    return _sequence_strings(dst.get("app_ids"))


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
