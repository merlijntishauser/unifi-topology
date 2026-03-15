"""Tests for snapshot serialization of Edge objects."""

from __future__ import annotations

from unifi_topology.model.connection import ConnectionInfo
from unifi_topology.model.snapshot import edge_from_dict, edge_to_dict
from unifi_topology.model.topology import Edge


class TestEdgeSerialization:
    def test_round_trip(self):
        edge = Edge(
            left="switch-1",
            right="ap-1",
            label="Port 24",
            poe=True,
            wireless=False,
            speed=1000,
            channel=None,
            vlans=(1, 10, 20),
            active_vlans=(1, 10),
            is_trunk=True,
        )
        restored = edge_from_dict(edge_to_dict(edge))
        assert restored.left == "switch-1"
        assert restored.right == "ap-1"
        assert restored.poe is True
        assert restored.vlans == (1, 10, 20)
        assert restored.is_trunk is True

    def test_defaults_for_missing_fields(self):
        edge = edge_from_dict({"left": "a", "right": "b"})
        assert edge.left == "a"
        assert edge.poe is False
        assert edge.vlans == ()


class TestEdgeWithConnection:
    def test_edge_round_trip_with_connection(self):
        conn = ConnectionInfo(
            signal_dbm=-50,
            noise_dbm=-90,
            tx_rate_mbps=866,
            rx_rate_mbps=400,
            satisfaction=95,
            quality="excellent",
        )
        edge = Edge(
            left="ap-1",
            right="client-1",
            label="WiFi",
            poe=False,
            wireless=True,
            speed=None,
            channel=36,
            vlans=(),
            active_vlans=(),
            is_trunk=False,
            connection=conn,
        )
        data = edge_to_dict(edge)
        assert data["connection"] is not None
        assert data["connection"]["signal_dbm"] == -50
        restored = edge_from_dict(data)
        assert restored.connection is not None
        assert restored.connection.signal_dbm == -50
        assert restored.connection.quality == "excellent"
        assert restored.wireless is True
        assert restored.channel == 36
