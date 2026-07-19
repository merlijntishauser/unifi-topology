"""Compatibility tests for scalar topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model._topology_port_coerce import (
    _aggregation_group,
    _as_float,
    _as_group_id,
    _as_int,
)
from unifi_topology.model.helpers import as_bool, as_list


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
