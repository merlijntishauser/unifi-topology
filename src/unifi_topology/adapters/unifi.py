"""UniFi API integration."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from ..model.vlans import build_vlan_info, normalize_networks
from . import _cache as _cache_impl
from . import _fetch as _fetch_impl
from . import _retry as _retry_impl
from .config import Config
from .unifi_api import UnifiAuthError, UnifiClient

logger = logging.getLogger(__name__)

__all__ = [
    "_acquire_cache_lock",
    "_cache_dir",
    "_cache_key",
    "_cache_lock",
    "_cache_lock_path",
    "_cache_ttl_seconds",
    "_call_with_retries",
    "_connect_and_fetch",
    "_create_client",
    "_device_lldp_value",
    "_device_uplink_fields",
    "_evict_client",
    "_fetch_cached",
    "_fetch_payload_clients",
    "_get_or_create_client",
    "_is_cache_dir_safe",
    "_is_rate_limited",
    "_is_retryable",
    "_load_cache",
    "_load_cache_with_age",
    "_log_retry_failure",
    "_release_cache_lock",
    "_request_timeout_seconds",
    "_retry_attempts",
    "_retry_backoff_seconds",
    "_save_cache",
    "_serialize_device_for_cache",
    "_serialize_devices_for_cache",
    "_serialize_lldp_entries",
    "_serialize_network_for_cache",
    "_serialize_network_table",
    "_serialize_networks_for_cache",
    "_serialize_port_entry",
    "_serialize_port_table",
    "_serialize_uplink",
    "_sleep_before_retry",
    "clear_client_cache",
    "fetch_clients",
    "fetch_device_stats",
    "fetch_devices",
    "fetch_firewall_groups",
    "fetch_firewall_policies",
    "fetch_firewall_zones",
    "fetch_networks",
    "fetch_payload",
    "invalidate_cache",
    "swap_firewall_policy_order",
    "toggle_firewall_policy",
]

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

_is_retryable = _retry_impl._is_retryable
_request_timeout_seconds = _retry_impl._request_timeout_seconds
_retry_attempts = _retry_impl._retry_attempts
_retry_backoff_seconds = _retry_impl._retry_backoff_seconds


_cache_lock = _cache_impl._cache_lock


# Extra cache-key parts used by some fetchers, keyed by cache prefix. Kept in
# sync with the cache_key_extra passed by the fetch_* functions so that
# invalidate_cache targets the same files.
_PREFIX_CACHE_KEY_EXTRAS: dict[str, tuple[tuple[str, ...], ...]] = {
    "devices": (("True",), ("False",)),
}


def _cache_key_extras(prefix: str) -> tuple[tuple[str, ...], ...]:
    return _PREFIX_CACHE_KEY_EXTRAS.get(prefix, ((),))


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
        for extra in _cache_key_extras(prefix):
            key = _cache_key(config.url, site_name, *extra)
            cache_path = _cache_dir() / f"{prefix}_{key}.json"
            removed += _remove_cache_file(cache_path)
    return removed


def _remove_cache_file(cache_path: Path) -> int:
    if not cache_path.exists():
        return 0
    try:
        with _cache_lock(cache_path):
            cache_path.unlink(missing_ok=True)
        logger.debug("Invalidated cache: %s", cache_path.name)
        return 1
    except OSError as exc:
        logger.warning("Failed to invalidate cache %s: %s", cache_path, exc)
        return 0


def _call_with_retries[T](operation: str, func: Callable[[], T]) -> T:
    attempts = _retry_attempts()
    backoff = _retry_backoff_seconds()
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - surface full error after retries
            last_exc = exc
            if not _is_retryable(exc):
                raise
            _log_retry_failure(operation, attempt, attempts, exc)
            _sleep_before_retry(attempt, attempts, backoff)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed {operation}")


def _log_retry_failure(operation: str, attempt: int, attempts: int, exc: Exception) -> None:
    logger.warning("Failed %s attempt %d/%d: %s", operation, attempt, attempts, exc)


def _sleep_before_retry(attempt: int, attempts: int, backoff: float) -> None:
    if attempt >= attempts or backoff <= 0:
        return
    time.sleep(backoff * attempt)


def _create_client(config: Config, *, is_udm_pro: bool) -> UnifiClient:
    return UnifiClient(
        url=config.url,
        username=config.user,
        password=config.password,
        api_key=config.api_key,
        is_udm_pro=is_udm_pro,
        verify_ssl=config.verify_ssl,
        request_timeout=_request_timeout_seconds(),
    )


_client_cache: dict[tuple[str, str, bool], UnifiClient] = {}

# Remembers which auth style (True=UDM Pro, False=legacy) authenticated for a
# controller URL, so a legacy controller is not re-probed with a doomed UDM
# login on every fetch (which trips rate limiting).
_auth_style_cache: dict[str, bool] = {}


def _client_cache_key(config: Config, *, is_udm_pro: bool) -> tuple[str, str, bool]:
    identity = config.user or config.api_key or ""
    return (config.url, identity, is_udm_pro)


def _get_or_create_client(config: Config, *, is_udm_pro: bool) -> UnifiClient:
    """Get a cached client or create a new one."""
    cache_key = _client_cache_key(config, is_udm_pro=is_udm_pro)
    client = _client_cache.get(cache_key)
    if client is not None:
        return client
    client = _create_client(config, is_udm_pro=is_udm_pro)
    _client_cache[cache_key] = client
    return client


def _evict_client(config: Config, *, is_udm_pro: bool) -> None:
    """Remove a cached client entry."""
    cache_key = _client_cache_key(config, is_udm_pro=is_udm_pro)
    _client_cache.pop(cache_key, None)


def clear_client_cache() -> None:
    """Clear all cached client sessions and the remembered auth styles."""
    _client_cache.clear()
    _auth_style_cache.clear()


def _connect_client(config: Config) -> UnifiClient:
    """Authenticate, preferring the remembered auth style for this URL."""
    remembered = _auth_style_cache.get(config.url)
    if remembered is not None:
        return _get_or_create_client(config, is_udm_pro=remembered)
    try:
        client = _get_or_create_client(config, is_udm_pro=True)
    except UnifiAuthError as exc:
        if _is_rate_limited(exc):
            raise
        logger.debug("UDM Pro authentication failed, retrying legacy auth")
        try:
            client = _get_or_create_client(config, is_udm_pro=False)
        except UnifiAuthError as legacy_exc:
            raise legacy_exc from exc
        _auth_style_cache[config.url] = False
        return client
    _auth_style_cache[config.url] = True
    return client


def _is_rate_limited(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) == 429


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
    client = _connect_client(config)
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
    return _fetch_impl.fetch_cached(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix=cache_prefix,
        operation=operation,
        api_call=api_call,
        serialize=serialize,
        cache_key_extra=cache_key_extra,
        connect_and_fetch=_connect_and_fetch,
    )


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
