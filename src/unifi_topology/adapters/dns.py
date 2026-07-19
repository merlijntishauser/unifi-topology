"""Reverse DNS hostname resolution."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

import dns.resolver
import dns.reversename

logger = logging.getLogger(__name__)

_MAX_DNS_WORKERS = 16


def _resolve_one(resolver: dns.resolver.Resolver, ip: str) -> tuple[str, str] | None:
    try:
        rev_name = dns.reversename.from_address(ip)
        answer = resolver.resolve(rev_name, "PTR")
        return ip, str(answer[0]).rstrip(".")
    except Exception:  # noqa: BLE001
        logger.debug("Reverse DNS lookup failed for %s", ip)
        return None


def resolve_hostnames(
    ips: list[str],
    dns_server: str,
    timeout: float = 2.0,
) -> dict[str, str]:
    """Reverse-resolve IPs to hostnames using a specific DNS server.

    Uses dnspython to query the given dns_server for PTR records concurrently.
    Returns {ip: hostname} for successful resolutions only. Per-IP failures are
    skipped (logged at debug level); an invalid dns_server is logged at warning.
    """
    resolver = dns.resolver.Resolver(configure=False)
    try:
        resolver.nameservers = [dns_server]
    except ValueError:
        logger.warning("Invalid DNS server address (must be an IP): %s", dns_server)
        return {}
    resolver.lifetime = timeout

    if not ips:
        return {}

    workers = min(len(ips), _MAX_DNS_WORKERS)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        resolved = executor.map(lambda ip: _resolve_one(resolver, ip), ips)
    return dict(entry for entry in resolved if entry is not None)
