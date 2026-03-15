"""Helpers for client map coverage tests."""

from unifi_topology.model.topology import Device


def switch_device(mac: str = "aa:bb:cc:dd:ee:ff", name: str = "Switch") -> Device:
    return Device(
        name=name,
        model_name="",
        model="",
        mac=mac,
        ip="",
        type="usw",
        lldp_info=[],
    )


def gateway_device(mac: str = "aa", name: str = "Gateway") -> Device:
    return Device(
        name=name,
        model_name="",
        model="",
        mac=mac,
        ip="",
        type="udm",
        lldp_info=[],
    )
