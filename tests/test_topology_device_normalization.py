"""Tests for topology device normalization entry points."""

from __future__ import annotations

import pytest

from unifi_topology.model.topology_coerce import coerce_device, normalize_devices


class TestCoerceDevice:
    def test_minimal_device(self):
        raw = {
            "name": "Test Switch",
            "mac": "aa:bb:cc:dd:ee:ff",
            "lldp_info": [],
        }
        device = coerce_device(raw)
        assert device.name == "Test Switch"
        assert device.mac == "aa:bb:cc:dd:ee:ff"

    def test_missing_name_raises(self):
        raw = {"mac": "aa:bb:cc:dd:ee:ff", "lldp_info": []}
        with pytest.raises(ValueError, match="missing name or mac"):
            coerce_device(raw)

    def test_missing_mac_raises(self):
        raw = {"name": "Switch", "lldp_info": []}
        with pytest.raises(ValueError, match="missing name or mac"):
            coerce_device(raw)

    def test_missing_lldp_with_uplink_uses_fallback(self, caplog):
        raw = {
            "name": "Test AP",
            "mac": "aa:bb:cc:dd:ee:ff",
            "uplink": {
                "uplink_mac": "11:22:33:44:55:66",
                "uplink_device_name": "Switch",
            },
        }
        with caplog.at_level("DEBUG"):
            device = coerce_device(raw)
        assert device.name == "Test AP"
        assert "missing LLDP info" in caplog.text

    def test_missing_lldp_without_uplink_raises(self):
        raw = {"name": "Orphan", "mac": "aa:bb:cc:dd:ee:ff"}
        with pytest.raises(ValueError, match="missing LLDP info"):
            coerce_device(raw)

    def test_model_display_name_priority(self):
        raw = {
            "name": "Switch",
            "mac": "aa:bb:cc:dd:ee:ff",
            "model_in_lts": "USW Pro 24",
            "model_name": "Generic Switch",
            "model": "USW-Pro-24",
            "lldp_info": [],
        }
        device = coerce_device(raw)
        assert device.model_name == "USW Pro 24"


class TestNormalizeDevices:
    def test_normalizes_list(self):
        raw_devices = [
            {"name": "A", "mac": "00:00:00:00:00:01", "lldp_info": []},
            {"name": "B", "mac": "00:00:00:00:00:02", "lldp_info": []},
        ]
        devices = normalize_devices(raw_devices)
        assert len(devices) == 2
        assert devices[0].name == "A"
        assert devices[1].name == "B"

    def test_skips_malformed_device_and_logs(self, caplog):
        import logging

        raw_devices = [
            {"name": "A", "mac": "00:00:00:00:00:01", "lldp_info": []},
            {"name": "B"},  # missing mac -> malformed
        ]
        with caplog.at_level(logging.WARNING):
            devices = normalize_devices(raw_devices)
        assert [d.name for d in devices] == ["A"]
        assert any("skipping" in r.message.lower() for r in caplog.records)


def test_coerce_lldp_tolerates_non_numeric_local_port_idx():
    from unifi_topology.model.lldp import coerce_lldp

    entry = coerce_lldp({"chassis_id": "aa", "port_id": "1", "local_port_idx": "eth0"})
    assert entry.local_port_idx is None
