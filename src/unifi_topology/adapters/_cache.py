"""Private cache and serialization helpers for the UniFi adapter."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import stat
import tempfile
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import IO

from ..model.helpers import as_list, first_attr, get_field
from ..model.lldp import coerce_lldp
from ..model.snapshot import lldp_entry_to_dict
from ..paths import resolve_cache_dir

logger = logging.getLogger(__name__)


def _cache_dir() -> Path:
    default_dir = ".cache/unifi_network_maps"
    if os.environ.get("PYTEST_CURRENT_TEST"):
        default_dir = str(Path(tempfile.gettempdir()) / f"unifi_network_maps_pytest_{os.getpid()}")
    value = os.environ.get("UNIFI_CACHE_DIR", default_dir)
    try:
        return resolve_cache_dir(value)
    except ValueError as exc:
        logger.warning("Invalid UNIFI_CACHE_DIR (%s); using default: %s", value, exc)
        return resolve_cache_dir(".cache/unifi_network_maps")


def _serialize_lldp_entries(value: object | None) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for entry in as_list(value):
        try:
            lldp = coerce_lldp(entry)
        except ValueError:
            continue
        serialized.append(lldp_entry_to_dict(lldp))
    return serialized


def _serialize_port_entry(entry: object) -> dict[str, object]:
    aggregation_group = first_attr(
        entry,
        "aggregation_group",
        "aggregation_id",
        "aggregate_id",
        "agg_id",
        "lag_id",
        "lag_group",
        "link_aggregation_group",
        "link_aggregation_id",
        "aggregate",
        "aggregated_by",
    )
    native_vlan = first_attr(
        entry,
        "native_networkconf_id",
        "port_vlan",
        "vlan",
        "native_vlan",
        "pvid",
    )
    tagged_vlans = first_attr(
        entry,
        "tagged_vlan_mgmt",
        "tagged_vlans",
        "vlan_trunk_mgmt",
        "allowed_vlans",
    )
    return {
        "port_idx": first_attr(entry, "port_idx", "portIdx"),
        "name": first_attr(entry, "name"),
        "ifname": first_attr(entry, "ifname"),
        "speed": first_attr(entry, "speed"),
        "up": first_attr(entry, "up"),
        "aggregation_group": aggregation_group,
        "port_poe": first_attr(entry, "port_poe"),
        "poe_enable": first_attr(entry, "poe_enable"),
        "poe_good": first_attr(entry, "poe_good"),
        "poe_power": first_attr(entry, "poe_power"),
        "native_vlan": native_vlan,
        "tagged_vlans": tagged_vlans,
        "wan_networkconf_id": first_attr(entry, "wan_networkconf_id"),
    }


def _serialize_port_table(value: object | None) -> list[dict[str, object]]:
    return [_serialize_port_entry(entry) for entry in as_list(value)]


def _serialize_uplink(value: object | None) -> dict[str, object] | None:
    if value is None:
        return None
    data = {
        "uplink_mac": first_attr(value, "uplink_mac", "uplink_device_mac"),
        "uplink_device_name": first_attr(value, "uplink_device_name", "uplink_name"),
        "uplink_remote_port": first_attr(value, "uplink_remote_port", "port_idx"),
    }
    if any(item is not None for item in data.values()):
        return data
    return None


def _device_lldp_value(device: object) -> object | None:
    lldp_info = get_field(device, "lldp_info")
    if lldp_info is None:
        lldp_info = get_field(device, "lldp")
    if lldp_info is None:
        lldp_info = get_field(device, "lldp_table")
    return lldp_info


def _device_uplink_fields(device: object) -> dict[str, object | None]:
    return {
        "uplink": _serialize_uplink(get_field(device, "uplink")),
        "last_uplink": _serialize_uplink(get_field(device, "last_uplink")),
        "uplink_mac": first_attr(device, "uplink_mac", "uplink_device_mac"),
        "uplink_device_name": get_field(device, "uplink_device_name"),
        "uplink_remote_port": get_field(device, "uplink_remote_port"),
        "last_uplink_mac": get_field(device, "last_uplink_mac"),
    }


def _serialize_network_table(value: object | None) -> list[dict[str, object]]:
    """Serialize network_table entries for cache (preserves VPN tunnel data)."""
    entries = as_list(value)
    return [dict(entry) for entry in entries if isinstance(entry, dict)]


def _serialize_device_for_cache(device: object) -> dict[str, object]:
    payload = {
        "name": get_field(device, "name"),
        "model_name": get_field(device, "model_name"),
        "model": get_field(device, "model"),
        "mac": get_field(device, "mac"),
        "ip": first_attr(device, "ip", "ip_address"),
        "type": first_attr(device, "type", "device_type"),
        "in_gateway_mode": get_field(device, "in_gateway_mode"),
        "displayable_version": first_attr(device, "displayable_version", "version"),
        "lldp_info": _serialize_lldp_entries(_device_lldp_value(device)),
        "port_table": _serialize_port_table(get_field(device, "port_table")),
        "network_table": _serialize_network_table(get_field(device, "network_table")),
    }
    payload.update(_device_uplink_fields(device))
    return payload


def _serialize_devices_for_cache(devices: Sequence[object]) -> list[dict[str, object]]:
    return [_serialize_device_for_cache(device) for device in devices]


def _serialize_network_for_cache(network: object) -> dict[str, object]:
    return {
        "_id": first_attr(network, "_id", "id", "network_id", "networkId"),
        "name": first_attr(network, "name", "network_name", "networkName"),
        "vlan": first_attr(network, "vlan", "vlan_id", "vlanId", "vlanid"),
        "vlan_enabled": first_attr(network, "vlan_enabled", "vlanEnabled"),
        "purpose": first_attr(network, "purpose"),
        "enabled": first_attr(network, "enabled", "wan_enabled"),
    }


def _serialize_networks_for_cache(networks: Sequence[object]) -> list[dict[str, object]]:
    return [_serialize_network_for_cache(network) for network in networks]


def _cache_lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_cache_lock(lock_file: IO[str]) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)


def _release_cache_lock(lock_file: IO[str]) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextmanager
def _cache_lock(path: Path) -> Iterator[None]:
    lock_path = _cache_lock_path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            _acquire_cache_lock(lock_file)
            yield
        finally:
            try:
                _release_cache_lock(lock_file)
            except OSError:
                logger.debug("Failed to release cache lock %s", lock_path)


def _is_cache_dir_safe(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        logger.warning("Failed to stat cache dir %s: %s", path, exc)
        return False
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        logger.warning("Cache dir %s is group/world-writable; skipping cache", path)
        return False
    return True


def _cache_ttl_seconds() -> int:
    value = os.environ.get("UNIFI_CACHE_TTL_SECONDS", "").strip()
    if not value:
        return 3600
    if value.isdigit():
        return int(value)
    logger.warning("Invalid UNIFI_CACHE_TTL_SECONDS value: %s", value)
    return 3600


def _cache_key(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:24]


def _load_cache(path: Path, ttl_seconds: int) -> Sequence[object] | None:
    data, age = _load_cache_with_age(path)
    if data is None:
        return None
    if ttl_seconds <= 0:
        return None
    if age is None or age > ttl_seconds:
        return None
    return data


def _load_cache_with_age(path: Path) -> tuple[Sequence[object] | None, float | None]:
    if not path.exists():
        return None, None
    try:
        with _cache_lock(path):
            payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("Failed to read cache %s: %s", path, exc)
        return None, None
    if not isinstance(payload, dict):
        logger.debug("Cached payload at %s is not a dict", path)
        return None, None
    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, int | float):
        return None, None
    data = payload.get("data")
    if not isinstance(data, list):
        logger.debug("Cached payload at %s is not a list", path)
        return None, None
    return data, time.time() - timestamp


def _save_cache(path: Path, data: Sequence[object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not _is_cache_dir_safe(path.parent):
            return
        payload = {"timestamp": time.time(), "data": data}
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with _cache_lock(path):
            tmp_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
            tmp_path.replace(path)
    except Exception as exc:
        logger.debug("Failed to write cache %s: %s", path, exc)
