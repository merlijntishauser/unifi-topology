"""Private helpers for WAN and VPN label formatting."""

from __future__ import annotations

from ..model.topology import VpnTunnel, WanInfo, WanInterface


def _format_wan_speed(speed_mbps: int | None) -> str | None:
    """Format speed in Mbps to human-readable string (e.g., 10GbE, 100MbE)."""
    if speed_mbps is None or speed_mbps == 0:
        return None
    if speed_mbps >= 1000:
        gbps = speed_mbps / 1000
        if gbps == int(gbps):
            return f"{int(gbps)}GbE"
        return f"{gbps:.1f}GbE"
    return f"{speed_mbps}MbE"


def _format_wan_speed_line(
    wan: WanInterface,
    *,
    include_speed: bool,
) -> str:
    speed_parts: list[str] = []
    if include_speed and wan.link_speed and wan.enabled:
        speed_parts.append(f"Link {_format_wan_speed(wan.link_speed)}")
    if wan.isp_speed:
        speed_parts.append(f"ISP {wan.isp_speed}")
    return " / ".join(speed_parts)


def _disabled_wan_interface_line(wan: WanInterface, prefix: str) -> str:
    label = wan.label or prefix
    return f"{prefix}: {label} (disabled)"


def _dual_wan_interface_line(
    wan: WanInterface,
    prefix: str,
    *,
    include_speed: bool,
) -> str:
    line = f"{prefix}: {wan.label or prefix}"
    speed_str = _format_wan_speed_line(wan, include_speed=include_speed)
    if speed_str:
        line += f" ({speed_str})"
    status = "(active)" if wan.enabled else "(disabled)"
    return f"{line} {status}"


def _format_wan_interface_line(
    wan: WanInterface,
    prefix: str,
    *,
    is_dual: bool,
    include_speed: bool = True,
) -> str:
    """Format a single WAN interface line."""
    if not wan.enabled and prefix == "WAN2":
        return _disabled_wan_interface_line(wan, prefix)
    if is_dual:
        return _dual_wan_interface_line(wan, prefix, include_speed=include_speed)
    return wan.label or prefix


def _build_single_wan_label_lines(wan: WanInterface) -> list[str]:
    label_lines = [wan.label or "WAN1"]
    speed_line = _format_wan_speed_line(wan, include_speed=True)
    if speed_line:
        label_lines.append(speed_line)
    if wan.ip_address:
        label_lines.append(wan.ip_address)
    return label_lines


def _build_dual_wan_label_lines(wan_info: WanInfo) -> list[str]:
    label_lines: list[str] = []
    if wan_info.wan1:
        label_lines.append(_format_wan_interface_line(wan_info.wan1, "WAN1", is_dual=True))
    if wan_info.wan2:
        label_lines.append(_format_wan_interface_line(wan_info.wan2, "WAN2", is_dual=True))
    if wan_info.wan1 and wan_info.wan1.ip_address:
        label_lines.append(wan_info.wan1.ip_address)
    return label_lines


def _build_wan_label_lines(wan_info: WanInfo) -> list[str]:
    """Build label lines for WAN display."""
    if wan_info.wan2 is not None:
        return _build_dual_wan_label_lines(wan_info)
    if wan_info.wan1 is None:
        return []
    return _build_single_wan_label_lines(wan_info.wan1)


def _build_vpn_label_lines(tunnels: list[VpnTunnel]) -> list[str]:
    """Build label lines for VPN tunnel display."""
    lines: list[str] = []
    for tunnel in tunnels:
        status = "UP" if tunnel.up else "DOWN"
        lines.append(f"{tunnel.name} ({status})")
    return lines
