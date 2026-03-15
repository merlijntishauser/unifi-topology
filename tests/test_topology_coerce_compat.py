"""Compatibility-focused topology tests for coercion and helper paths."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from unifi_topology.model.helpers import as_bool, as_list
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import UplinkInfo
from unifi_topology.model.topology_coerce import (
    _aggregation_group,
    _as_float,
    _as_group_id,
    _as_int,
    _get_model_display_name,
    _parse_uplink,
    _poe_ports_from_device,
    _uplink_info,
    coerce_device,
)


def test_coerce_device_uses_lldp_fallback():
    class DeviceWithLldp:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = [LLDPEntry("bb", "1")]
        port_table = []

    device = coerce_device(DeviceWithLldp())
    assert device.lldp_info[0].chassis_id == "bb"


def test_coerce_device_uses_lldp_table_fallback():
    class DeviceWithLldpTable:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        lldp_table = [LLDPEntry("bb", "1")]
        port_table = []

    device = coerce_device(DeviceWithLldpTable())
    assert device.lldp_info[0].chassis_id == "bb"


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


@pytest.fixture()
def device_with_uplink_no_lldp():
    class MissingLldpWithUplink:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        uplink = {"uplink_mac": "bb", "uplink_device_name": "Gateway", "uplink_remote_port": 1}
        port_table = []

    return MissingLldpWithUplink()


def test_coerce_device_allows_uplink_when_lldp_missing(device_with_uplink_no_lldp):
    assert coerce_device(device_with_uplink_no_lldp).lldp_info == []


def test_coerce_device_tracks_poe_false_when_power_invalid():
    class DeviceWithPort:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = [LLDPEntry("bb", "1")]
        port_table = [{"port_idx": 1, "poe_power": "bad"}]

    assert coerce_device(DeviceWithPort()).poe_ports[1] is False


def test_coerce_device_missing_name_raises():
    with pytest.raises(ValueError):
        coerce_device(SimpleNamespace(name=None, mac="aa", lldp_info=[]))


def test_coerce_device_missing_lldp_raises():
    with pytest.raises(ValueError):
        coerce_device(SimpleNamespace(name="Dev", mac="aa", lldp_info=None, lldp=None))


def test_poe_ports_from_device_skips_missing_port_idx():
    assert _poe_ports_from_device(SimpleNamespace(port_table=[{"poe_enable": True}])) == {}


def test_poe_ports_from_device_reads_dict_power():
    assert _poe_ports_from_device(SimpleNamespace(port_table=[{"port_idx": 2, "poe_power": "1.2"}])) == {
        2: True
    }


def test_poe_ports_from_device_reads_portidx_key():
    assert _poe_ports_from_device(SimpleNamespace(port_table=[{"portIdx": 3, "poe_enable": True}])) == {
        3: True
    }


def test_as_group_id_handles_types():
    assert _as_group_id(None) is None
    assert _as_group_id(True) is None
    assert _as_group_id(5) == "5"
    assert _as_group_id(" lag1 ") == "lag1"
    assert _as_group_id(" ") is None
    assert _as_group_id(object()) is None


def test_aggregation_group_reads_dict_key():
    assert _aggregation_group({"lag_id": "lag5"}) == "lag5"


def test_aggregation_group_handles_missing_keys():
    assert _aggregation_group({"aggregation_group": None}) is None


def test_aggregation_group_reads_object_attr():
    class PortEntry:
        aggregation_group = None
        agg_id = "agg2"

    assert _aggregation_group(PortEntry()) == "agg2"


def test_as_bool_int_true():
    assert as_bool(1) is True


def test_as_bool_str_truthy():
    assert as_bool("yes") is True


def test_as_float_none_returns_zero():
    assert _as_float(None) == 0.0


def test_as_float_invalid_str_returns_zero():
    assert _as_float("nope") == 0.0


def test_as_float_int_returns_float():
    assert _as_float(2) == 2.0


def test_as_float_unknown_type_returns_zero():
    assert _as_float([]) == 0.0


def test_as_list_coerces_iterable():
    assert as_list(("a", "b")) == ["a", "b"]


def test_as_int_parses_digit_string():
    assert _as_int("7") == 7


def test_parse_uplink_reads_object_fields():
    parsed = _parse_uplink(
        SimpleNamespace(uplink_device_mac="aa", uplink_device_name="Core", port_idx=3)
    )
    assert parsed == UplinkInfo(mac="aa", name="Core", port=3)


def test_uplink_info_falls_back_to_last_uplink_mac():
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        last_uplink_mac="bb",
    )
    uplink, last_uplink = _uplink_info(device)
    assert uplink is None
    assert last_uplink == UplinkInfo(mac="bb", name=None, port=None)


def test_get_model_display_name_prefers_model_in_lts():
    device = SimpleNamespace(
        model_in_lts="USW Flex 2.5G 8 PoE",
        model_name="USW-Flex-2.5G-8-PoE",
        model="USWFLEXPOE8",
    )
    assert _get_model_display_name(device) == "USW Flex 2.5G 8 PoE"


def test_get_model_display_name_uses_model_in_eol():
    assert _get_model_display_name(SimpleNamespace(model_in_eol="USW Pro 24", model="USWPRO24")) == "USW Pro 24"


def test_get_model_display_name_uses_shortname():
    assert _get_model_display_name(SimpleNamespace(shortname="USW Mini", model="USWMINI")) == "USW Mini"


def test_get_model_display_name_falls_back_to_model_name():
    assert _get_model_display_name(SimpleNamespace(model_name="Dream Machine", model="UDM")) == "Dream Machine"


def test_get_model_display_name_returns_none_without_candidates():
    assert _get_model_display_name(SimpleNamespace(model="USWFLEX")) is None


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
