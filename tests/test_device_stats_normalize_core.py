"""Tests for core device stats normalization behavior."""

import pytest

from unifi_topology.model.device_stats_coerce import normalize_device_stats

pytestmark = pytest.mark.unit


class TestNormalizeDeviceStatsCore:
    def test_realistic_device(self):
        raw = [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "name": "Core Switch",
                "model": "USW-Enterprise-24-PoE",
                "type": "usw",
                "uptime": 172800,
                "system-stats": {"cpu": "12.5", "mem": "38.2"},
                "general_temperature": 42,
                "tx_bytes": 500000000,
                "rx_bytes": 300000000,
                "num_sta": 15,
                "version": "7.1.68",
                "port_table": [
                    {
                        "port_idx": 1,
                        "poe_mode": "auto",
                        "poe_power": "5.2",
                    },
                    {
                        "port_idx": 2,
                        "poe_mode": "off",
                        "poe_power": "0.0",
                    },
                    {
                        "port_idx": 3,
                        "name": "uplink",
                    },
                ],
                "total_max_power": 95.0,
            }
        ]
        result = normalize_device_stats(raw)
        assert len(result) == 1
        dev = result[0]
        assert dev.mac == "aa:bb:cc:dd:ee:ff"
        assert dev.name == "Core Switch"
        assert dev.model == "USW-Enterprise-24-PoE"
        assert dev.type == "switch"
        assert dev.uptime == 172800
        assert dev.cpu == 12.5
        assert dev.mem == 38.2
        assert dev.temperature == 42.0
        assert dev.tx_bytes == 500000000
        assert dev.rx_bytes == 300000000
        assert dev.num_sta == 15
        assert dev.version == "7.1.68"
        assert len(dev.poe_ports) == 2
        assert dev.poe_ports[0].port_idx == 1
        assert dev.poe_ports[0].poe_power == 5.2
        assert dev.poe_ports[0].poe_mode == "auto"
        assert dev.poe_ports[1].port_idx == 2
        assert dev.poe_ports[1].poe_power == 0.0
        assert dev.poe_budget == 95.0

    def test_minimal_data(self):
        raw = [{"mac": "11:22:33:44:55:66"}]
        result = normalize_device_stats(raw)
        assert len(result) == 1
        dev = result[0]
        assert dev.mac == "11:22:33:44:55:66"
        assert dev.name == ""
        assert dev.model == ""
        assert dev.type == ""
        assert dev.uptime == 0
        assert dev.cpu == 0.0
        assert dev.mem == 0.0
        assert dev.temperature is None
        assert dev.tx_bytes == 0
        assert dev.rx_bytes == 0
        assert dev.num_sta == 0
        assert dev.version == ""
        assert dev.poe_ports == []
        assert dev.poe_budget is None

    def test_empty_input(self):
        result = normalize_device_stats([])
        assert result == []

    def test_type_normalization_ugw(self):
        raw = [{"mac": "aa", "type": "ugw"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "gateway"

    def test_type_normalization_udm(self):
        raw = [{"mac": "aa", "type": "udm"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "gateway"

    def test_type_normalization_usw(self):
        raw = [{"mac": "aa", "type": "usw"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "switch"

    def test_type_normalization_uap(self):
        raw = [{"mac": "aa", "type": "uap"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "ap"

    def test_type_unknown_preserved(self):
        raw = [{"mac": "aa", "type": "uxg"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "uxg"

    def test_multiple_devices(self):
        raw = [
            {"mac": "aa", "type": "usw", "name": "Switch"},
            {"mac": "bb", "type": "uap", "name": "AP"},
        ]
        result = normalize_device_stats(raw)
        assert len(result) == 2
        assert result[0].name == "Switch"
        assert result[0].type == "switch"
        assert result[1].name == "AP"
        assert result[1].type == "ap"
