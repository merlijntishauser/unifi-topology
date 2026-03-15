import unifi_topology.render.svg_labels as svg_labels_module


def test_extract_port_text_non_port_prefix():
    assert svg_labels_module._extract_port_text("eth0") is None


def test_wrap_text_splits_without_space():
    assert svg_labels_module._wrap_text("ABCDEFGHI", max_len=4) == ["ABCD", "EFGHI"]


def test_label_metrics_empty_lines():
    assert svg_labels_module._label_metrics([], font_size=10, padding_x=4, padding_y=3) == (
        8.0,
        6.0,
    )


def test_compact_edge_label_swaps_when_nodes_reversed():
    label = "B: Port 1 <-> A: Port 2"
    assert (
        svg_labels_module._compact_edge_label(label, left_node="A", right_node="B")
        == "A Port 2 <-> Port 1"
    )


def test_compact_edge_label_right_port_only():
    assert svg_labels_module._compact_edge_label("Switch <-> Port 2") == "Port 2"


def test_compact_edge_label_left_port_only():
    assert svg_labels_module._compact_edge_label("Port 1 <-> Switch") == "Port 1"


def test_compact_edge_label_no_ports_returns_label():
    assert svg_labels_module._compact_edge_label("A <-> B") == "A <-> B"
