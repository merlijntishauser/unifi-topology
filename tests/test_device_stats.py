"""Tests for device stats normalization."""

import pytest

from unifi_topology.model.device_stats import DeviceStats, PoePortStats
from unifi_topology.model.device_stats_coerce import normalize_device_stats

pytestmark = pytest.mark.unit


class TestPoePortStats:
    def test_creation(self):
        port = PoePortStats(port_idx=1, poe_power=12.5, poe_mode="auto")
        assert port.port_idx == 1
        assert port.poe_power == 12.5
        assert port.poe_mode == "auto"

    def test_frozen(self):
        port = PoePortStats(port_idx=1, poe_power=12.5, poe_mode="auto")
        with pytest.raises(AttributeError):
            port.poe_power = 0.0  # type: ignore[misc]


class TestDeviceStats:
    def test_field_types(self):
        stats = DeviceStats(
            mac="aa:bb:cc:dd:ee:ff",
            name="Switch",
            model="USW-24-PoE",
            type="switch",
            uptime=86400,
            cpu=15.2,
            mem=42.8,
            temperature=45.0,
            tx_bytes=1000000,
            rx_bytes=2000000,
            num_sta=5,
            version="7.1.68",
            poe_ports=[PoePortStats(port_idx=1, poe_power=5.0, poe_mode="auto")],
            poe_budget=95.0,
        )
        assert stats.mac == "aa:bb:cc:dd:ee:ff"
        assert stats.type == "switch"
        assert stats.uptime == 86400
        assert stats.cpu == 15.2
        assert stats.temperature == 45.0
        assert len(stats.poe_ports) == 1
        assert stats.poe_budget == 95.0

    def test_defaults(self):
        stats = DeviceStats(
            mac="aa:bb:cc:dd:ee:ff",
            name="AP",
            model="U6-Pro",
            type="ap",
            uptime=0,
            cpu=0.0,
            mem=0.0,
        )
        assert stats.temperature is None
        assert stats.tx_bytes == 0
        assert stats.rx_bytes == 0
        assert stats.num_sta == 0
        assert stats.version == ""
        assert stats.poe_ports == []
        assert stats.poe_budget is None

    def test_frozen(self):
        stats = DeviceStats(
            mac="aa:bb:cc:dd:ee:ff",
            name="AP",
            model="U6-Pro",
            type="ap",
            uptime=0,
            cpu=0.0,
            mem=0.0,
        )
        with pytest.raises(AttributeError):
            stats.cpu = 100.0  # type: ignore[misc]


class TestNormalizeDeviceStats:
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
