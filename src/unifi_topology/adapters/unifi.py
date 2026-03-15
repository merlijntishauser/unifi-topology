"""UniFi API integration."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from ..model.vlans import build_vlan_info, normalize_networks
from . import _cache as _cache_impl
from . import _retry as _retry_impl
from .config import Config
from .unifi_api import UnifiAuthError, UnifiClient

logger = logging.getLogger(__name__)

_acquire_cache_lock = _cache_impl._acquire_cache_lock
_cache_dir = _cache_impl._cache_dir
_cache_key = _cache_impl._cache_key
_cache_lock_path = _cache_impl._cache_lock_path
_cache_ttl_seconds = _cache_impl._cache_ttl_seconds
_device_lldp_value = _cache_impl._device_lldp_value
_device_uplink_fields = _cache_impl._device_uplink_fields
_is_cache_dir_safe = _cache_impl._is_cache_dir_safe
_load_cache = _cache_impl._load_cache
_load_cache_with_age = _cache_impl._load_cache_with_age
_release_cache_lock = _cache_impl._release_cache_lock
_save_cache = _cache_impl._save_cache
_serialize_device_for_cache = _cache_impl._serialize_device_for_cache
_serialize_devices_for_cache = _cache_impl._serialize_devices_for_cache
_serialize_lldp_entries = _cache_impl._serialize_lldp_entries
_serialize_network_for_cache = _cache_impl._serialize_network_for_cache
_serialize_network_table = _cache_impl._serialize_network_table
_serialize_networks_for_cache = _cache_impl._serialize_networks_for_cache
_serialize_port_entry = _cache_impl._serialize_port_entry
_serialize_port_table = _cache_impl._serialize_port_table
_serialize_uplink = _cache_impl._serialize_uplink

_call_with_timeout = _retry_impl._call_with_timeout
_request_timeout_seconds = _retry_impl._request_timeout_seconds
_retry_attempts = _retry_impl._retry_attempts
_retry_backoff_seconds = _retry_impl._retry_backoff_seconds


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


def invalidate_cache(
    config: Config,
    *,
    prefixes: Sequence[str] = ("fw_policies",),
    site: str | None = None,
) -> int:
    """Remove cached data files matching the given prefixes.

    Returns the number of cache files removed.
    """
    site_name = site or config.site
    removed = 0
    for prefix in prefixes:
        cache_path = _cache_dir() / f"{prefix}_{_cache_key(config.url, site_name)}.json"
        if cache_path.exists():
            try:
                with _cache_lock(cache_path):
                    cache_path.unlink(missing_ok=True)
                removed += 1
                logger.debug("Invalidated cache: %s", cache_path.name)
            except OSError as exc:
                logger.warning("Failed to invalidate cache %s: %s", cache_path, exc)
    return removed


def _call_with_retries[T](operation: str, func: Callable[[], T]) -> T:
    attempts = _retry_attempts()
    backoff = _retry_backoff_seconds()
    timeout = _request_timeout_seconds()
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _call_with_timeout(operation, func, timeout)
        except Exception as exc:  # noqa: BLE001 - surface full error after retries
            last_exc = exc
            logger.warning("Failed %s attempt %d/%d: %s", operation, attempt, attempts, exc)
            if attempt < attempts and backoff > 0:
                time.sleep(backoff * attempt)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed {operation}")


def _create_client(config: Config, *, is_udm_pro: bool) -> UnifiClient:
    return UnifiClient(
        url=config.url,
        username=config.user,
        password=config.password,
        is_udm_pro=is_udm_pro,
        verify_ssl=config.verify_ssl,
        request_timeout=_request_timeout_seconds(),
    )


_client_cache: dict[tuple[str, str, bool], UnifiClient] = {}


def _get_or_create_client(config: Config, *, is_udm_pro: bool) -> UnifiClient:
    """Get a cached client or create a new one."""
    cache_key = (config.url, config.user, is_udm_pro)
    client = _client_cache.get(cache_key)
    if client is not None:
        return client
    client = _create_client(config, is_udm_pro=is_udm_pro)
    _client_cache[cache_key] = client
    return client


def _evict_client(config: Config, *, is_udm_pro: bool) -> None:
    """Remove a cached client entry."""
    cache_key = (config.url, config.user, is_udm_pro)
    _client_cache.pop(cache_key, None)


def clear_client_cache() -> None:
    """Clear all cached client sessions."""
    _client_cache.clear()


def _is_rate_limited(exc: Exception) -> bool:
    return "429" in str(exc)


def _connect_and_fetch(
    config: Config,
    operation: str,
    fetch_fn: Callable[[UnifiClient], Callable[[], Sequence[object]]],
) -> Sequence[object]:
    """Authenticate and fetch data, with UDM Pro / legacy auth fallback.

    On ``UnifiAuthError`` that isn't rate-limited, retries with
    legacy auth.  Any other error (rate limit, network, etc.) propagates
    to the caller's stale-cache handler.

    Reuses cached client sessions per config to avoid repeated logins.
    """
    try:
        client = _get_or_create_client(config, is_udm_pro=True)
    except UnifiAuthError as exc:
        if _is_rate_limited(exc):
            raise
        logger.debug("UDM Pro authentication failed, retrying legacy auth")
        client = _get_or_create_client(config, is_udm_pro=False)

    return _call_with_retries(operation, fetch_fn(client))


def _fetch_cached(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
    cache_prefix: str,
    operation: str,
    api_call: Callable[[UnifiClient, str], Callable[[], Sequence[object]]],
    serialize: Callable[[Sequence[object]], Sequence[object]] | None = None,
    cache_key_extra: Sequence[str] = (),
) -> Sequence[object]:
    """Generic fetch-with-cache for any UniFi API resource."""
    site_name = site or config.site
    ttl_seconds = _cache_ttl_seconds()
    key_parts = (config.url, site_name, *cache_key_extra)
    cache_path = _cache_dir() / f"{cache_prefix}_{_cache_key(*key_parts)}.json"
    cache_safe = use_cache and _is_cache_dir_safe(cache_path.parent)
    if cache_safe:
        cached = _load_cache(cache_path, ttl_seconds)
        if cached is not None:
            logger.debug("Using cached %s (%d)", operation, len(cached))
            return cached

    def _make_fetch(client: UnifiClient) -> Callable[[], Sequence[object]]:
        return api_call(client, site_name)

    try:
        data = _connect_and_fetch(config, operation, _make_fetch)
    except Exception as exc:  # noqa: BLE001 - fallback to cache
        stale_cached, cache_age = _load_cache_with_age(cache_path) if cache_safe else (None, None)
        if stale_cached is not None:
            logger.warning(
                "%s failed; using stale cache (%ds old): %s",
                operation.capitalize(),
                int(cache_age or 0),
                exc,
            )
            return stale_cached
        raise
    if use_cache:
        _save_cache(cache_path, serialize(data) if serialize else data)
    logger.debug("Fetched %d %s", len(data), operation)
    return data


def fetch_devices(
    config: Config,
    *,
    site: str | None = None,
    detailed: bool = True,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch devices from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="devices",
        operation="devices",
        api_call=lambda client, site_name: lambda: client.get_devices(site_name, detailed=detailed),
        serialize=_serialize_devices_for_cache,
        cache_key_extra=(str(detailed),),
    )


def fetch_clients(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch active clients from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="clients",
        operation="clients",
        api_call=lambda client, site_name: lambda: client.get_clients(site_name),
    )


def fetch_networks(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch network inventory from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="networks",
        operation="networks",
        api_call=lambda client, site_name: lambda: client.get_networkconf(site_name),
        serialize=_serialize_networks_for_cache,
    )


def fetch_payload(
    config: Config,
    *,
    site: str | None = None,
    include_clients: bool = True,
    use_cache: bool = True,
) -> dict[str, list[object] | list[dict[str, object]]]:
    """Fetch devices, clients, and VLAN inventory for payload output."""
    devices = list(fetch_devices(config, site=site, detailed=True, use_cache=use_cache))
    clients = _fetch_payload_clients(
        config,
        site=site,
        include_clients=include_clients,
        use_cache=use_cache,
    )
    networks = list(fetch_networks(config, site=site, use_cache=use_cache))
    normalized_networks = normalize_networks(networks)
    vlan_info = build_vlan_info(clients, normalized_networks)
    return {
        "devices": devices,
        "clients": clients,
        "networks": normalized_networks,
        "vlan_info": vlan_info,
    }


def fetch_firewall_zones(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch firewall zone definitions from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="fw_zones",
        operation="firewall zones",
        api_call=lambda client, site_name: lambda: client.get_firewall_zones(site_name),
    )


def fetch_firewall_policies(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch zone-based firewall policies from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="fw_policies",
        operation="firewall policies",
        api_call=lambda client, site_name: lambda: client.get_firewall_policies(site_name),
    )


def fetch_firewall_groups(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
) -> Sequence[object]:
    """Fetch firewall address/port groups from UniFi Controller."""
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="fw_groups",
        operation="firewall groups",
        api_call=lambda client, site_name: lambda: client.get_firewall_groups(site_name),
    )


def _fetch_payload_clients(
    config: Config,
    *,
    site: str | None,
    include_clients: bool,
    use_cache: bool,
) -> list[object]:
    if not include_clients:
        return []
    return list(fetch_clients(config, site=site, use_cache=use_cache))


def toggle_firewall_policy(
    config: Config,
    policy_id: str,
    *,
    enabled: bool,
    site: str | None = None,
) -> None:
    """Toggle a firewall policy's enabled state and invalidate cache."""
    site_name = site or config.site
    client = _get_or_create_client(config, is_udm_pro=True)
    client.update_firewall_policy(site_name, policy_id, {"enabled": enabled})
    clear_client_cache()
    invalidate_cache(config, site=site)


def fetch_device_stats(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = False,
) -> Sequence[object]:
    """Fetch device statistics from the UniFi controller.

    Returns raw device dicts with system-stats fields (CPU, memory,
    temperature, traffic counters, PoE).  Pass the result to
    ``normalize_device_stats()`` to get typed ``DeviceStats`` objects.

    Cache is bypassed by default since metrics polling needs fresh data.
    """
    return _fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix="device_stats",
        operation="device stats",
        api_call=lambda client, site_name: lambda: client.get_devices(site_name, detailed=True),
    )


def swap_firewall_policy_order(
    config: Config,
    policy_id_a: str,
    policy_id_b: str,
    *,
    site: str | None = None,
) -> None:
    """Swap the index of two firewall policies and invalidate cache."""
    site_name = site or config.site
    client = _get_or_create_client(config, is_udm_pro=True)
    client.swap_firewall_policy_order(site_name, policy_id_a, policy_id_b)
    clear_client_cache()
    invalidate_cache(config, site=site)
