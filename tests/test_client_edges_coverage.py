"""Coverage tests for client edge building and collapsing."""

from unifi_topology.model.clients import build_client_edges, collapse_client_edges
from unifi_topology.model.topology import Edge


def test_collapse_client_edges_collapses_generic_clients():
    """Generic clients should be collapsed into cluster nodes."""
    edges = [
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:01"),
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:02"),
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:03"),
    ]
    node_types = {
        "aa:bb:cc:00:00:01": "switch",
        "cc:cc:cc:00:00:01": "client",
        "cc:cc:cc:00:00:02": "client",
        "cc:cc:cc:00:00:03": "client",
    }
    node_names: dict[str, str] = {"aa:bb:cc:00:00:01": "Switch"}
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types, node_names)
    assert client_counts == {"aa:bb:cc:00:00:01": 3}
    assert len(collapsed_edges) == 1
    assert collapsed_edges[0].left == "aa:bb:cc:00:00:01"
    assert collapsed_edges[0].right == "aa:bb:cc:00:00:01__cluster"
    assert node_types["aa:bb:cc:00:00:01__cluster"] == "client_cluster"
    assert node_names["aa:bb:cc:00:00:01__cluster"] == "Switch (3 clients)"
    assert "cc:cc:cc:00:00:01" not in node_types
    assert "cc:cc:cc:00:00:02" not in node_types
    assert "cc:cc:cc:00:00:03" not in node_types


def test_collapse_client_edges_preserves_non_client_edges():
    """Non-client edges should be preserved as-is."""
    edges = [
        Edge(left="aa:bb:cc:00:00:01", right="aa:bb:cc:00:00:02"),
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:01"),
    ]
    node_types = {
        "aa:bb:cc:00:00:01": "switch",
        "aa:bb:cc:00:00:02": "ap",
        "cc:cc:cc:00:00:01": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"aa:bb:cc:00:00:01": 1}
    ap_edges = [e for e in collapsed_edges if e.right == "aa:bb:cc:00:00:02"]
    assert len(ap_edges) == 1
    cluster_edges = [e for e in collapsed_edges if "__cluster" in e.right]
    assert len(cluster_edges) == 1


def test_collapse_client_edges_multiple_devices():
    """Clients from different devices should be collapsed separately."""
    edges = [
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:01"),
        Edge(left="aa:bb:cc:00:00:01", right="cc:cc:cc:00:00:02"),
        Edge(left="aa:bb:cc:00:00:02", right="cc:cc:cc:00:00:03"),
    ]
    node_types = {
        "aa:bb:cc:00:00:01": "switch",
        "aa:bb:cc:00:00:02": "switch",
        "cc:cc:cc:00:00:01": "client",
        "cc:cc:cc:00:00:02": "client",
        "cc:cc:cc:00:00:03": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"aa:bb:cc:00:00:01": 2, "aa:bb:cc:00:00:02": 1}
    assert len(collapsed_edges) == 2


def test_collapse_client_edges_no_clients():
    """When there are no client edges, nothing should be collapsed."""
    edges = [
        Edge(left="aa:bb:cc:00:00:01", right="aa:bb:cc:00:00:02"),
    ]
    node_types = {
        "aa:bb:cc:00:00:01": "switch",
        "aa:bb:cc:00:00:02": "ap",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {}
    assert collapsed_edges == edges


def test_build_client_edges_includes_vlan():
    """Client VLAN should be included in the edge."""
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Desktop",
            "mac": "11:22:33:44:55:01",
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
            "vlan": 100,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges[0].vlans == (100,)
    assert edges[0].active_vlans == (100,)
