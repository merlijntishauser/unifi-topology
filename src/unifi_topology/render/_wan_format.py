"""Shared WAN link-speed formatting for the SVG and Mermaid renderers."""

from __future__ import annotations


def format_wan_speed(speed_mbps: int | None) -> str | None:
    """Format a speed in Mbps as a human-readable string (e.g. 10GbE, 100MbE)."""
    if speed_mbps is None or speed_mbps == 0:
        return None
    if speed_mbps >= 1000:
        gbps = speed_mbps / 1000
        if gbps == int(gbps):
            return f"{int(gbps)}GbE"
        return f"{gbps:.1f}GbE"
    return f"{speed_mbps}MbE"
