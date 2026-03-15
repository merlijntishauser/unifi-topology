"""Tests for device stats metric extraction behavior."""

import pytest

from unifi_topology.model.device_stats_coerce import normalize_device_stats

pytestmark = pytest.mark.unit


class TestNormalizeDeviceStatsMetrics:
    def test_traffic_from_stat_nested(self):
        raw = [
            {
                "mac": "aa",
                "stat": {"tx_bytes": 1234, "rx_bytes": 5678},
            }
        ]
        result = normalize_device_stats(raw)
        assert result[0].tx_bytes == 1234
        assert result[0].rx_bytes == 5678

    def test_traffic_direct_takes_priority(self):
        raw = [
            {
                "mac": "aa",
                "tx_bytes": 100,
                "rx_bytes": 200,
                "stat": {"tx_bytes": 999, "rx_bytes": 888},
            }
        ]
        result = normalize_device_stats(raw)
        assert result[0].tx_bytes == 100
        assert result[0].rx_bytes == 200

    def test_temperature_from_system_stats_temps(self):
        raw = [
            {
                "mac": "aa",
                "system-stats": {"cpu": "5", "mem": "20", "temps": {"CPU": "55.0"}},
            }
        ]
        result = normalize_device_stats(raw)
        assert result[0].temperature == 55.0

    def test_temperature_general_takes_priority(self):
        raw = [
            {
                "mac": "aa",
                "general_temperature": 42,
                "system-stats": {"cpu": "5", "mem": "20", "temps": {"CPU": "55.0"}},
            }
        ]
        result = normalize_device_stats(raw)
        assert result[0].temperature == 42.0

    def test_port_table_non_poe_ports_skipped(self):
        raw = [
            {
                "mac": "aa",
                "port_table": [
                    {"port_idx": 1, "name": "eth0"},
                    {"port_idx": 2, "poe_mode": "auto", "poe_power": 3.5},
                ],
            }
        ]
        result = normalize_device_stats(raw)
        assert len(result[0].poe_ports) == 1
        assert result[0].poe_ports[0].port_idx == 2

    def test_port_table_non_dict_entries_skipped(self):
        raw = [{"mac": "aa", "port_table": ["not-a-dict", None, 42]}]
        result = normalize_device_stats(raw)
        assert result[0].poe_ports == []

    def test_system_stats_non_dict_ignored(self):
        raw = [{"mac": "aa", "system-stats": "invalid"}]
        result = normalize_device_stats(raw)
        assert result[0].cpu == 0.0
        assert result[0].mem == 0.0
