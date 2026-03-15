"""Tests for numeric topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model.topology_coerce import (
    _aggregation_group,
    _as_float,
    _as_group_id,
    _as_int,
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
