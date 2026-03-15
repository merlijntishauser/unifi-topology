"""Tests for device stats model classes."""

import pytest

from unifi_topology.model.device_stats import DeviceStats, PoePortStats

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
