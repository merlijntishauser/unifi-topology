"""Tests for SVG port label layout helpers."""

from __future__ import annotations

from unifi_topology.render.svg_labels import _format_port_label_lines


class TestFormatPortLabelLines:
    def test_single_port(self):
        lines = _format_port_label_lines("Port 24", prefix="uplink", max_chars=30)
        assert len(lines) == 1
        assert "Port 24" in lines[0]

    def test_bidirectional_creates_two_lines(self):
        lines = _format_port_label_lines(
            "Switch: Port 1 <-> AP: Port 0",
            prefix="uplink",
            max_chars=30,
        )
        assert len(lines) == 2

    def test_truncates_long_labels(self):
        lines = _format_port_label_lines(
            "Very Long Device Name: Port 24",
            prefix="uplink",
            max_chars=20,
        )
        assert all(len(line) <= 20 for line in lines)

    def test_prefix_used_in_label(self):
        lines = _format_port_label_lines("Port 5", prefix="switch", max_chars=30)
        assert "switch" in lines[0]

    def test_bidirectional_second_line_uses_local(self):
        lines = _format_port_label_lines(
            "Switch A: Port 4 <-> Switch B: Port 8",
            prefix="Switch A",
            max_chars=30,
        )
        assert len(lines) == 2
        assert "Switch A" in lines[0]
        assert lines[1].startswith("local:")

    def test_unidirectional_uses_prefix_not_local(self):
        lines = _format_port_label_lines("Port 5", prefix="Switch TV Kast", max_chars=30)
        assert "Switch TV Kast" in lines[0]
        assert "local" not in lines[0].lower()
