"""Tests for edge VLAN enrichment helpers."""

from __future__ import annotations

from unifi_topology.model.edges import enrich_edges_with_active_vlans
from unifi_topology.model.topology import Edge


def test_enrich_edges_with_active_vlans_basic():
    edges = [Edge("Switch", "AP", vlans=(10, 20, 30))]
    client_edges = [
        Edge("Switch", "Client1", active_vlans=(10,)),
        Edge("AP", "Client2", active_vlans=(20,)),
    ]
    result = enrich_edges_with_active_vlans(edges, client_edges)
    assert len(result) == 1
    assert result[0].active_vlans == (10, 20)


def test_enrich_edges_with_active_vlans_no_overlap():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    client_edges = [Edge("Switch", "Client1", active_vlans=(99,))]
    assert enrich_edges_with_active_vlans(edges, client_edges)[0].active_vlans == ()


def test_enrich_edges_with_active_vlans_empty_clients():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    assert enrich_edges_with_active_vlans(edges, [])[0].active_vlans == ()


def test_enrich_edges_preserves_other_fields():
    edges = [
        Edge(
            "Switch",
            "AP",
            label="Port 1",
            poe=True,
            wireless=True,
            speed=1000,
            channel=36,
            vlans=(10,),
            is_trunk=False,
        )
    ]
    result = enrich_edges_with_active_vlans(edges, [Edge("Switch", "Client1", active_vlans=(10,))])
    assert result[0].label == "Port 1"
    assert result[0].poe is True
    assert result[0].wireless is True
    assert result[0].speed == 1000
    assert result[0].channel == 36
    assert result[0].is_trunk is False
    assert result[0].active_vlans == (10,)
