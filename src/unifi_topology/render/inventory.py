"""Device inventory table rendering."""

from __future__ import annotations

from ..model.inventory import DeviceInfo


def _inventory_table_columns(include_hostname: bool) -> tuple[str, str]:
    if include_hostname:
        return (
            "| Name | Type | Model | IP | Hostname | MAC | Firmware |",
            "|------|------|-------|----|----------|-----|----------|",
        )
    return (
        "| Name | Type | Model | IP | MAC | Firmware |",
        "|------|------|-------|----|-----|----------|",
    )


def _inventory_row(device: DeviceInfo, *, include_hostname: bool) -> str:
    if include_hostname:
        return (
            f"| {device.name} | {device.device_type} | {device.model_name} | {device.ip}"
            f" | {device.hostname or ''} | {device.mac} | {device.firmware} |"
        )
    return (
        f"| {device.name} | {device.device_type} | {device.model_name} | {device.ip}"
        f" | {device.mac} | {device.firmware} |"
    )


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

    header, separator = _inventory_table_columns(include_hostname)
    rows = [_inventory_row(device, include_hostname=include_hostname) for device in inventory]
    return "\n".join([header, separator, *rows]) + "\n"
