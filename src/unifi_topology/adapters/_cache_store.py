"""Private cache storage helpers for the UniFi adapter."""

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
    if value != default_dir:
        try:
            return resolve_cache_dir(default_dir)
        except ValueError as exc:
            logger.warning(
                "Default cache dir unusable (%s); caching disabled: %s", default_dir, exc
            )
    # Best-effort fallback so fetching degrades to no-cache instead of raising;
    # _is_cache_dir_safe and _save_cache still gate any actual read/write.
    return Path(default_dir).expanduser().resolve(strict=False)


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


def _read_cache_payload(path: Path) -> object | None:
    if not path.exists():
        return None
    try:
        with _cache_lock(path):
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("Failed to read cache %s: %s", path, exc)
        return None


def _cache_payload_timestamp(payload: object, *, path: Path) -> int | float | None:
    if not isinstance(payload, dict):
        logger.debug("Cached payload at %s is not a dict", path)
        return None
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, int | float):
        return timestamp
    return None


def _cache_payload_data(
    payload: object,
    *,
    path: Path,
) -> Sequence[object] | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, list):
        return data
    logger.debug("Cached payload at %s is not a list", path)
    return None


def _load_cache_with_age(path: Path) -> tuple[Sequence[object] | None, float | None]:
    payload = _read_cache_payload(path)
    if payload is None:
        return None, None
    timestamp = _cache_payload_timestamp(payload, path=path)
    if timestamp is None:
        return None, None
    data = _cache_payload_data(payload, path=path)
    if data is None:
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
            # Cache files hold MACs/IPs/hostnames; keep them owner-only.
            os.chmod(tmp_path, 0o600)
            tmp_path.replace(path)
    except Exception as exc:
        logger.debug("Failed to write cache %s: %s", path, exc)
