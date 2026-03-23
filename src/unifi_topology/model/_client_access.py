"""Private helpers for reading client attachment and connection data."""

from __future__ import annotations

from collections.abc import Iterable

from ._raw import RawRecord, nested_records
from .connection import ConnectionInfo, classify_signal_quality
from .helpers import get_field, normalize_mac
from .ports import extract_port_number


def _client_nested_records(client: object) -> tuple[RawRecord, ...]:
    return tuple(nested_records(client, "uplink", "last_uplink"))


def client_node_id(client: object) -> str | None:
    """Get the client's own MAC address as a normalized node ID."""
    mac = get_field(client, "mac")
    if isinstance(mac, str) and mac.strip():
        return normalize_mac(mac)
    return None


def client_uplink_mac(client: object) -> str | None:
    """Get the MAC address of the device this client is connected to."""
    record = RawRecord(client)
    mac = record.text("ap_mac", "sw_mac", "uplink_mac", "uplink_device_mac", "last_uplink_mac")
    if mac:
        return mac
    for nested in _client_nested_records(client):
        mac = nested.text("uplink_mac", "uplink_device_mac")
        if mac:
            return mac
    return None


def _client_port_values(client: object) -> Iterable[object | None]:
    """Yield all possible port values from client data."""
    record = RawRecord(client)
    for key in ("uplink_remote_port", "sw_port", "ap_port", "port_idx"):
        yield record.get(key)
    for nested in _client_nested_records(client):
        for nested_key in ("uplink_remote_port", "port_idx"):
            yield nested.get(nested_key)


def _parse_port_value(value: object | None) -> int | None:
    """Parse a port value to int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
        return extract_port_number(stripped)
    return None


def client_uplink_port(client: object) -> int | None:
    """Get the port number this client is connected to."""
    for value in _client_port_values(client):
        parsed = _parse_port_value(value)
        if parsed is not None:
            return parsed
    return None


def _client_is_wired(client: object) -> bool:
    """Check if client is wired."""
    return bool(get_field(client, "is_wired"))


def _client_channel(client: object) -> int | None:
    """Get wireless channel for client."""
    record = RawRecord(client)
    for key in ("channel", "radio_channel", "wifi_channel"):
        value = record.integer(key)
        if value is not None:
            return value
    return None


def _client_vlan(client: object) -> int | None:
    """Get VLAN ID for client."""
    record = RawRecord(client)
    for key in ("vlan", "vlan_id", "vlanId", "vlanid"):
        value = record.integer(key)
        if value is not None and value > 0:
            return value
    return None


def _metric_int(value: object | None) -> int | None:
    if isinstance(value, int | float):
        return int(value)
    return None


def _extract_connection_info(client: object) -> ConnectionInfo | None:
    """Extract connection quality metrics for wireless clients."""
    if _client_is_wired(client):
        return None

    record = RawRecord(client)
    signal_dbm = _metric_int(record.get("signal"))
    noise_dbm = _metric_int(record.get("noise"))
    tx_rate_mbps = _metric_int(record.get("tx_rate"))
    rx_rate_mbps = _metric_int(record.get("rx_rate"))
    satisfaction_val = _metric_int(record.get("satisfaction"))

    return ConnectionInfo(
        signal_dbm=signal_dbm,
        noise_dbm=noise_dbm,
        tx_rate_mbps=tx_rate_mbps,
        rx_rate_mbps=rx_rate_mbps,
        satisfaction=satisfaction_val,
        quality=classify_signal_quality(signal_dbm),
    )
