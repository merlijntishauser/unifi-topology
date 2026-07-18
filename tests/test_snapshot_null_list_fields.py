"""Snapshot loaders must tolerate JSON null for list-valued fields."""

from unifi_topology.model.snapshot import edge_from_dict, port_info_from_dict


def test_edge_from_dict_tolerates_null_vlans():
    edge = edge_from_dict({"left": "a", "right": "b", "vlans": None, "active_vlans": None})
    assert edge.vlans == ()
    assert edge.active_vlans == ()


def test_port_info_from_dict_tolerates_null_tagged_vlans():
    port = port_info_from_dict({"port_idx": 1, "tagged_vlans": None})
    assert port.tagged_vlans == ()
