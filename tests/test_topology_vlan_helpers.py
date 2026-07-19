"""Tests for VLAN topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model._topology_port_coerce import _coerce_vlan_list, _resolve_vlan_id


class TestCoerceVlanList:
    def test_none_returns_empty(self):
        assert _coerce_vlan_list(None) == ()

    def test_special_string_auto(self):
        assert _coerce_vlan_list("auto") == ()

    def test_special_string_block_all(self):
        assert _coerce_vlan_list("block_all") == ()

    def test_special_string_all(self):
        assert _coerce_vlan_list("ALL") == ()

    def test_special_string_none(self):
        assert _coerce_vlan_list("none") == ()

    def test_empty_string(self):
        assert _coerce_vlan_list("") == ()

    def test_comma_separated_string(self):
        assert _coerce_vlan_list("10, 20, 30") == (10, 20, 30)

    def test_single_int(self):
        assert _coerce_vlan_list(100) == (100,)

    def test_list_of_ints(self):
        assert _coerce_vlan_list([30, 10, 20]) == (10, 20, 30)

    def test_list_with_network_ids(self):
        network_map = {"network_a": 10, "network_b": 20}
        result = _coerce_vlan_list(["network_a", 30, "network_b"], network_map)
        assert result == (10, 20, 30)

    def test_list_with_invalid_items(self):
        assert _coerce_vlan_list([10, "invalid", 20]) == (10, 20)

    def test_other_type_returns_empty(self):
        assert _coerce_vlan_list({"not": "a list"}) == ()


class TestResolveVlanId:
    def test_int_value(self):
        assert _resolve_vlan_id(100) == 100

    def test_string_int_value(self):
        assert _resolve_vlan_id("50") == 50

    def test_network_id_with_map(self):
        network_map = {"my_network": 25}
        assert _resolve_vlan_id("my_network", network_map) == 25

    def test_unknown_network_id_returns_none(self):
        network_map = {"my_network": 25}
        assert _resolve_vlan_id("unknown", network_map) is None

    def test_none_returns_none(self):
        assert _resolve_vlan_id(None) is None
