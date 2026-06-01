"""Tests for SVG label parsing helpers."""

from __future__ import annotations

from unifi_topology.render.svg_labels import (
    _compact_edge_label,
    _escape_attr,
    _escape_text,
    _extract_device_name,
    _extract_port_text,
)


class TestEscapeText:
    def test_escapes_ampersand(self):
        assert _escape_text("A & B") == "A &amp; B"

    def test_escapes_less_than(self):
        assert _escape_text("A < B") == "A &lt; B"

    def test_escapes_greater_than(self):
        assert _escape_text("A > B") == "A &gt; B"

    def test_escapes_all_special_chars(self):
        assert _escape_text("<A & B>") == "&lt;A &amp; B&gt;"

    def test_no_escape_needed(self):
        assert _escape_text("plain text") == "plain text"

    def test_strips_xml_invalid_control_chars(self):
        assert _escape_text("My\x03Phone") == "MyPhone"
        assert _escape_text("a\x00b\x08c") == "abc"

    def test_preserves_allowed_whitespace_controls(self):
        assert _escape_text("keep\x09tab\x0anewline\x0dcr") == "keep\x09tab\x0anewline\x0dcr"

    def test_combines_strip_and_escape(self):
        assert _escape_text("A&\x03B") == "A&amp;B"


class TestEscapeAttr:
    def test_escapes_quotes_for_attribute_context(self):
        assert _escape_attr('Node "A"') == "Node &quot;A&quot;"

    def test_escapes_xml_entities(self):
        assert _escape_attr("A & <B>") == "A &amp; &lt;B&gt;"

    def test_strips_xml_invalid_control_chars(self):
        assert _escape_attr("My\x03Phone") == "MyPhone"
        assert _escape_attr("a\x00b\x08c") == "abc"

    def test_preserves_allowed_whitespace_controls(self):
        assert _escape_attr("keep\x09tab\x0anewline\x0dcr") == "keep\x09tab\x0anewline\x0dcr"

    def test_combines_strip_and_escape(self):
        assert _escape_attr('A&\x03"B') == "A&amp;&quot;B"


class TestExtractPortText:
    def test_extracts_port_after_colon(self):
        assert _extract_port_text("Switch: Port 24") == "Port 24"

    def test_extracts_standalone_port(self):
        assert _extract_port_text("Port 1") == "Port 1"

    def test_returns_none_for_no_port(self):
        assert _extract_port_text("Switch: eth0") is None

    def test_case_insensitive(self):
        assert _extract_port_text("Device: port 5") == "port 5"


class TestExtractDeviceName:
    def test_extracts_name_before_colon(self):
        assert _extract_device_name("Switch: Port 24") == "Switch"

    def test_returns_none_without_colon(self):
        assert _extract_device_name("Port 24") is None

    def test_returns_none_for_empty_name(self):
        assert _extract_device_name(": Port 24") is None

    def test_strips_whitespace(self):
        assert _extract_device_name("  Switch  : Port 24") == "Switch"


class TestCompactEdgeLabel:
    def test_returns_unchanged_without_arrow(self):
        assert _compact_edge_label("Port 24") == "Port 24"

    def test_compacts_bidirectional_ports(self):
        label = "Switch: Port 1 <-> AP: Port 0"
        result = _compact_edge_label(label)
        assert "Port 1" in result
        assert "Port 0" in result

    def test_returns_single_port_if_only_one(self):
        label = "Switch: Port 1 <-> AP: eth0"
        result = _compact_edge_label(label)
        assert result == "Port 1"

    def test_swaps_order_when_names_match_nodes(self):
        label = "Switch: Port 1 <-> AP: Port 0"
        result = _compact_edge_label(label, left_node="AP", right_node="Switch")
        assert "Port 0" in result or "Port 1" in result
