"""Private retry and timeout helpers for the UniFi adapter."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


def _retry_attempts() -> int:
    value = os.environ.get("UNIFI_RETRY_ATTEMPTS", "").strip()
    if not value:
        return 2
    if value.isdigit():
        return min(max(1, int(value)), 20)
    logger.warning("Invalid UNIFI_RETRY_ATTEMPTS value: %s", value)
    return 2


def _retry_backoff_seconds() -> float:
    value = os.environ.get("UNIFI_RETRY_BACKOFF_SECONDS", "").strip()
    if not value:
        return 0.5
    try:
        return min(max(0.0, float(value)), 60.0)
    except ValueError:
        logger.warning("Invalid UNIFI_RETRY_BACKOFF_SECONDS value: %s", value)
        return 0.5


def _request_timeout_seconds() -> float | None:
    value = os.environ.get("UNIFI_REQUEST_TIMEOUT_SECONDS", "").strip()
    if not value:
        return None
    try:
        return min(max(0.0, float(value)), 300.0)
    except ValueError:
        logger.warning("Invalid UNIFI_REQUEST_TIMEOUT_SECONDS value: %s", value)
        return None


def _call_with_timeout[T](operation: str, func: Callable[[], T], timeout: float | None) -> T:
    if timeout is None or timeout <= 0:
        return func()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"{operation} timed out after {timeout:.2f}s") from exc
