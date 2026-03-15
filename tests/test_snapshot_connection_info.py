"""Tests for snapshot serialization of ConnectionInfo objects."""

from __future__ import annotations

from unifi_topology.model.connection import ConnectionInfo
from unifi_topology.model.snapshot import connection_info_from_dict, connection_info_to_dict


class TestConnectionInfoSerialization:
    def test_connection_info_to_dict(self):
        conn = ConnectionInfo(
            signal_dbm=-55,
            noise_dbm=-95,
            tx_rate_mbps=400,
            rx_rate_mbps=300,
            satisfaction=85,
            quality="good",
        )
        data = connection_info_to_dict(conn)
        assert data["signal_dbm"] == -55
        assert data["noise_dbm"] == -95
        assert data["tx_rate_mbps"] == 400
        assert data["rx_rate_mbps"] == 300
        assert data["satisfaction"] == 85
        assert data["quality"] == "good"

    def test_connection_info_from_dict(self):
        conn = connection_info_from_dict(
            {
                "signal_dbm": -60,
                "noise_dbm": -90,
                "tx_rate_mbps": 200,
                "rx_rate_mbps": 150,
                "satisfaction": 75,
                "quality": "fair",
            }
        )
        assert conn.signal_dbm == -60
        assert conn.noise_dbm == -90
        assert conn.tx_rate_mbps == 200
        assert conn.rx_rate_mbps == 150
        assert conn.satisfaction == 75
        assert conn.quality == "fair"

    def test_connection_info_round_trip(self):
        conn = ConnectionInfo(signal_dbm=-70, quality="fair")
        restored = connection_info_from_dict(connection_info_to_dict(conn))
        assert restored.signal_dbm == conn.signal_dbm
        assert restored.quality == conn.quality

    def test_connection_info_from_dict_with_defaults(self):
        conn = connection_info_from_dict({})
        assert conn.signal_dbm is None
        assert conn.noise_dbm is None
        assert conn.quality is None
