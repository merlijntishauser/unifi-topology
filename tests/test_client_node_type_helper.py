"""Classified client categories must be treated as clients everywhere."""

from unifi_topology.model.classify import is_client_node_type
from unifi_topology.model.clients import collapse_client_edges
from unifi_topology.model.topology import Edge
from unifi_topology.render.svg_edges import _edge_opacity


def test_is_client_node_type_covers_classified_categories():
    assert is_client_node_type("camera")
    assert is_client_node_type("client")
    assert not is_client_node_type("switch")
    assert not is_client_node_type("client_cluster")
    assert not is_client_node_type(None)


def test_collapse_client_edges_collapses_classified_clients():
    edges = [Edge("sw", "pc"), Edge("sw", "cam"), Edge("sw", "phone")]
    node_types = {"sw": "switch", "pc": "client", "cam": "camera", "phone": "phone"}
    collapsed = collapse_client_edges(edges, node_types, {"sw": "Switch"})
    assert collapsed.client_counts == {"sw": 3}
    assert collapsed.node_names["sw__cluster"] == "Switch (3 clients)"
    assert "cam" not in collapsed.node_types


def test_edge_opacity_dims_classified_client_edges():
    assert _edge_opacity({"sw": "switch", "cam": "camera"}, Edge("sw", "cam")) == 0.5
    assert _edge_opacity({"sw": "switch", "ap": "ap"}, Edge("sw", "ap")) == 1.0
