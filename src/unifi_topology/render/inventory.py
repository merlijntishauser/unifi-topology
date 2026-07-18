"""Device inventory table rendering."""

from __future__ import annotations

from ..model.inventory import DeviceInfo
from ._markdown_tables import escape_markdown, markdown_table_lines


def _inventory_headers(include_hostname: bool) -> list[str]:
    if include_hostname:
        return ["Name", "Type", "Model", "IP", "Hostname", "MAC", "Firmware"]
    return ["Name", "Type", "Model", "IP", "MAC", "Firmware"]


def _inventory_row(device: DeviceInfo, *, include_hostname: bool) -> list[str]:
    if include_hostname:
        return [
            device.name,
            device.device_type,
            device.model_name,
            device.ip,
            device.hostname or "",
            device.mac,
            device.firmware,
        ]
    return [
        device.name,
        device.device_type,
        device.model_name,
        device.ip,
        device.mac,
        device.firmware,
    ]


def render_device_inventory_table(
    inventory: list[DeviceInfo],
    *,
    include_hostname: bool = True,
) -> str:
    """Render a markdown table of infrastructure devices.

    When include_hostname is False, the Hostname column is omitted.
    """
    if not inventory:
        return ""

    headers = _inventory_headers(include_hostname)
    rows = [_inventory_row(device, include_hostname=include_hostname) for device in inventory]
    lines = markdown_table_lines(headers, rows, escape=escape_markdown)
    return "\n".join(lines) + "\n"
