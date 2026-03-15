"""Shared helpers for dual render tests."""

from unifi_topology.model.topology import Edge


def basic_edges() -> list[Edge]:
    return [
        Edge("GW", "SW", vlans=(1, 10), active_vlans=(1, 10)),
        Edge("SW", "AP", vlans=(10,), active_vlans=(10,)),
    ]


def basic_node_types() -> dict[str, str]:
    return {"GW": "gateway", "SW": "switch", "AP": "ap"}
