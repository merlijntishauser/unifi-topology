"""Coverage tests for client edge building and collapsing."""

from unifi_topology.model.clients import build_client_edges, collapse_client_edges
from unifi_topology.model.topology import Edge


def test_collapse_client_edges_collapses_generic_clients():
    """Generic clients should be collapsed into cluster nodes."""
    edges = [
        Edge(left="Switch", right="Laptop1"),
        Edge(left="Switch", right="Laptop2"),
        Edge(left="Switch", right="Laptop3"),
    ]
    node_types = {
        "Switch": "switch",
        "Laptop1": "client",
        "Laptop2": "client",
        "Laptop3": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch": 3}
    assert len(collapsed_edges) == 1
    assert collapsed_edges[0].left == "Switch"
    assert collapsed_edges[0].right == "Switch (3 clients)"
    assert node_types["Switch (3 clients)"] == "client_cluster"
    assert "Laptop1" not in node_types
    assert "Laptop2" not in node_types
    assert "Laptop3" not in node_types


def test_collapse_client_edges_preserves_non_client_edges():
    """Non-client edges should be preserved as-is."""
    edges = [
        Edge(left="Switch", right="AP One"),
        Edge(left="Switch", right="Laptop"),
    ]
    node_types = {
        "Switch": "switch",
        "AP One": "ap",
        "Laptop": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch": 1}
    ap_edges = [e for e in collapsed_edges if e.right == "AP One"]
    assert len(ap_edges) == 1
    cluster_edges = [e for e in collapsed_edges if "clients" in e.right]
    assert len(cluster_edges) == 1


def test_collapse_client_edges_multiple_devices():
    """Clients from different devices should be collapsed separately."""
    edges = [
        Edge(left="Switch A", right="Client1"),
        Edge(left="Switch A", right="Client2"),
        Edge(left="Switch B", right="Client3"),
    ]
    node_types = {
        "Switch A": "switch",
        "Switch B": "switch",
        "Client1": "client",
        "Client2": "client",
        "Client3": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch A": 2, "Switch B": 1}
    assert len(collapsed_edges) == 2


def test_collapse_client_edges_no_clients():
    """When there are no client edges, nothing should be collapsed."""
    edges = [
        Edge(left="Switch", right="AP One"),
    ]
    node_types = {
        "Switch": "switch",
        "AP One": "ap",
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
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
            "vlan": 100,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges[0].vlans == (100,)
    assert edges[0].active_vlans == (100,)
