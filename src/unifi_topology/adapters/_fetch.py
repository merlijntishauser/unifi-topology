"""Private fetch orchestration helpers for the UniFi adapter."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ._cache_store import (
    _cache_dir,
    _cache_key,
    _cache_ttl_seconds,
    _is_cache_dir_safe,
    _load_cache,
    _load_cache_with_age,
    _save_cache,
)
from .config import Config
from .unifi_api import UnifiClient

logger = logging.getLogger(__name__)

ConnectAndFetch = Callable[
    [Config, str, Callable[[UnifiClient], Callable[[], Sequence[object]]]],
    Sequence[object],
]


@dataclass(frozen=True)
class _FetchPlan:
    operation: str
    site_name: str
    cache_path: Path
    cache_safe: bool
    use_cache: bool


def _build_fetch_plan(
    config: Config,
    *,
    site: str | None,
    use_cache: bool,
    cache_prefix: str,
    operation: str,
    cache_key_extra: Sequence[str],
) -> _FetchPlan:
    site_name = site or config.site
    key_parts = (config.url, site_name, *cache_key_extra)
    cache_path = _cache_dir() / f"{cache_prefix}_{_cache_key(*key_parts)}.json"
    cache_safe = use_cache and _is_cache_dir_safe(cache_path.parent)
    return _FetchPlan(
        operation=operation,
        site_name=site_name,
        cache_path=cache_path,
        cache_safe=cache_safe,
        use_cache=use_cache,
    )


def _load_fresh_cache(plan: _FetchPlan, *, ttl_seconds: int) -> Sequence[object] | None:
    if not plan.cache_safe:
        return None
    cached = _load_cache(plan.cache_path, ttl_seconds)
    if cached is None:
        return None
    logger.debug("Using cached %s (%d)", plan.operation, len(cached))
    return cached


def _load_stale_cache(plan: _FetchPlan, *, exc: Exception) -> Sequence[object] | None:
    if not plan.cache_safe:
        return None
    stale_cached, cache_age = _load_cache_with_age(plan.cache_path)
    if stale_cached is None:
        return None
    logger.warning(
        "%s failed; using stale cache (%ds old): %s",
        plan.operation.capitalize(),
        int(cache_age or 0),
        exc,
    )
    return stale_cached


def _save_fetched_data(
    plan: _FetchPlan,
    *,
    data: Sequence[object],
    serialize: Callable[[Sequence[object]], Sequence[object]] | None,
) -> None:
    if not plan.use_cache:
        return
    _save_cache(plan.cache_path, serialize(data) if serialize else data)


def fetch_cached(
    config: Config,
    *,
    site: str | None = None,
    use_cache: bool = True,
    cache_prefix: str,
    operation: str,
    api_call: Callable[[UnifiClient, str], Callable[[], Sequence[object]]],
    serialize: Callable[[Sequence[object]], Sequence[object]] | None = None,
    cache_key_extra: Sequence[str] = (),
    connect_and_fetch: ConnectAndFetch,
) -> Sequence[object]:
    """Fetch a resource with fresh-cache and stale-cache fallback handling."""
    plan = _build_fetch_plan(
        config,
        site=site,
        use_cache=use_cache,
        cache_prefix=cache_prefix,
        operation=operation,
        cache_key_extra=cache_key_extra,
    )
    cached = _load_fresh_cache(plan, ttl_seconds=_cache_ttl_seconds())
    if cached is not None:
        return cached

    def _make_fetch(client: UnifiClient) -> Callable[[], Sequence[object]]:
        return api_call(client, plan.site_name)

    try:
        data = connect_and_fetch(config, operation, _make_fetch)
    except Exception as exc:  # noqa: BLE001 - preserve stale-cache fallback
        stale_cached = _load_stale_cache(plan, exc=exc)
        if stale_cached is not None:
            return stale_cached
        raise

    _save_fetched_data(plan, data=data, serialize=serialize)
    logger.debug("Fetched %d %s", len(data), operation)
    return data
