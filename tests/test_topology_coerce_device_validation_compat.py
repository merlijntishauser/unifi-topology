"""Compatibility-focused tests for device coercion validation behavior."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology_coerce import coerce_device


def test_coerce_device_requires_name():
    class MissingName:
        name = ""
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = [LLDPEntry("bb", "1")]
        port_table = []

    with pytest.raises(ValueError):
        coerce_device(MissingName())


def test_coerce_device_requires_lldp():
    class MissingLldp:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        port_table = []

    with pytest.raises(ValueError):
        coerce_device(MissingLldp())


def test_coerce_device_missing_name_raises():
    with pytest.raises(ValueError):
        coerce_device(SimpleNamespace(name=None, mac="aa", lldp_info=[]))


def test_coerce_device_missing_lldp_raises():
    with pytest.raises(ValueError):
        coerce_device(SimpleNamespace(name="Dev", mac="aa", lldp_info=None, lldp=None))


def test_coerce_device_uses_model_in_lts_for_model_name():
    device = SimpleNamespace(
        name="Switch",
        mac="aa:bb:cc:dd:ee:ff",
        model_in_lts="USW Flex 2.5G 8 PoE",
        model="USWFLEXPOE8",
        ip="",
        type="usw",
        lldp_info=[],
        port_table=[],
    )

    result = coerce_device(device)

    assert result.model_name == "USW Flex 2.5G 8 PoE"
    assert result.model == "USWFLEXPOE8"
