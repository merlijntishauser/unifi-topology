"""Tests for private raw payload access helpers."""

from __future__ import annotations

from unifi_topology.model._raw import RawRecord, nested_records


class _PayloadObject:
    def __init__(self) -> None:
        self.name = "  Switch  "
        self.port_idx = "7"
        self.enabled = "true"
        self.uplink = {"uplink_mac": "aa:bb:cc:dd:ee:ff"}


def test_raw_record_reads_dict_fields() -> None:
    record = RawRecord({"name": " AP ", "port_idx": 4, "up": 1})

    assert record.text("name") == "AP"
    assert record.integer("port_idx") == 4
    assert record.optional_bool("up") is True


def test_raw_record_reads_object_fields() -> None:
    record = RawRecord(_PayloadObject())

    assert record.text("name") == "Switch"
    assert record.integer("port_idx") == 7
    assert record.optional_bool("enabled") is True


def test_raw_record_present_skips_empty_values() -> None:
    record = RawRecord({"aggregation_group": "", "lag_id": "agg-1"})

    assert record.present("aggregation_group", "lag_id", skip_values=(None, "", False)) == "agg-1"


def test_nested_records_yields_record_like_fields() -> None:
    payload = _PayloadObject()

    nested = tuple(nested_records(payload, "uplink", "last_uplink"))

    assert len(nested) == 1
    assert nested[0].text("uplink_mac") == "aa:bb:cc:dd:ee:ff"
