"""Private retry and timeout helpers for the UniFi adapter."""

from __future__ import annotations

import logging
import os

from .unifi_api import UnifiAuthError, UnifiError

logger = logging.getLogger(__name__)

_DEFAULT_REQUEST_TIMEOUT_SECONDS = 30.0

# HTTP statuses worth retrying: request timeout, rate limit, and 5xx.
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """Return whether an operation that raised *exc* is worth retrying.

    Retry by default; only known-deterministic failures are surfaced
    immediately. Authentication failures and 4xx API responses never succeed on
    retry and can trip controller rate limiting or account lockout.
    """
    if isinstance(exc, UnifiAuthError):
        return False
    if isinstance(exc, UnifiError):
        status = getattr(exc, "status_code", None)
        if status is not None and status not in _RETRYABLE_STATUS:
            return False
    return True


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
        return _DEFAULT_REQUEST_TIMEOUT_SECONDS
    try:
        return min(max(0.0, float(value)), 300.0)
    except ValueError:
        logger.warning("Invalid UNIFI_REQUEST_TIMEOUT_SECONDS value: %s", value)
        return _DEFAULT_REQUEST_TIMEOUT_SECONDS
