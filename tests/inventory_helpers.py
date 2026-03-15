"""Shared helpers for inventory tests."""

from unifi_topology.model.topology import Device


def make_device(
    name: str,
    ip: str,
    *,
    dtype: str = "usw",
    model_name: str = "Switch",
    mac: str = "aa:bb:cc:dd:ee:ff",
    version: str = "7.0.0",
) -> Device:
    return Device(
        name=name,
        model_name=model_name,
        model="US-24",
        mac=mac,
        ip=ip,
        type=dtype,
        lldp_info=[],
        version=version,
    )
