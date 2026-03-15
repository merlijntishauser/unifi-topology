"""Tests for scalar and VLAN topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model.topology_coerce import (
    _aggregation_group,
    _as_float,
    _as_group_id,
    _as_int,
    _coerce_vlan_list,
    _resolve_vlan_id,
)


class TestAsInt:
    def test_returns_int_directly(self):
        assert _as_int(42) == 42

    def test_parses_string(self):
        assert _as_int("123") == 123

    def test_invalid_string_returns_none(self):
        assert _as_int("abc") is None

    def test_none_returns_none(self):
        assert _as_int(None) is None

    def test_float_returns_none(self):
        assert _as_int(3.14) is None


class TestAsFloat:
    def test_returns_float_from_int(self):
        assert _as_float(10) == 10.0

    def test_returns_float_directly(self):
        assert _as_float(3.14) == 3.14

    def test_parses_string(self):
        assert _as_float("2.5") == 2.5

    def test_invalid_string_returns_zero(self):
        assert _as_float("not_a_number") == 0.0

    def test_none_returns_zero(self):
        assert _as_float(None) == 0.0


class TestAsGroupId:
    def test_none_returns_none(self):
        assert _as_group_id(None) is None

    def test_bool_returns_none(self):
        assert _as_group_id(True) is None
        assert _as_group_id(False) is None

    def test_int_returns_string(self):
        assert _as_group_id(5) == "5"

    def test_string_preserved(self):
        assert _as_group_id("lag1") == "lag1"

    def test_empty_string_returns_none(self):
        assert _as_group_id("  ") is None

    def test_other_types_return_none(self):
        assert _as_group_id([1, 2, 3]) is None


class TestAggregationGroup:
    def test_dict_with_aggregation_group(self):
        assert _aggregation_group({"aggregation_group": "lag1"}) == "lag1"

    def test_dict_with_lag_id(self):
        assert _aggregation_group({"lag_id": 2}) == 2

    def test_dict_with_none_value(self):
        assert _aggregation_group({"aggregation_group": None}) is None

    def test_dict_with_empty_string(self):
        assert _aggregation_group({"aggregation_group": ""}) is None

    def test_dict_with_false_value(self):
        assert _aggregation_group({"aggregation_group": False}) is None

    def test_non_dict_object_with_attribute(self):
        class MockPort:
            def __init__(self):
                self.lag_group = "lag2"

        assert _aggregation_group(MockPort()) == "lag2"

    def test_non_dict_object_no_match(self):
        class MockPort:
            def __init__(self):
                self.other_field = "value"

        assert _aggregation_group(MockPort()) is None


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
