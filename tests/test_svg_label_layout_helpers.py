"""Tests for SVG label layout helpers."""

from __future__ import annotations

from unifi_topology.render.svg_labels import (
    _format_port_label_lines,
    _label_metrics,
    _shorten_prefix,
    _wrap_text,
)


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


class TestWrapText:
    def test_no_wrap_short_text(self):
        assert _wrap_text("Short", max_len=24) == ["Short"]

    def test_wraps_at_space(self):
        lines = _wrap_text("Hello World Test", max_len=12)
        assert len(lines) == 2
        assert lines[0] == "Hello World"
        assert lines[1] == "Test"

    def test_wraps_at_max_len_if_no_space(self):
        lines = _wrap_text("NoSpacesHere", max_len=5)
        assert len(lines) == 2
        assert lines[0] == "NoSpa"
        assert lines[1] == "cesHere"

    def test_exact_length_no_wrap(self):
        text = "ExactLength"
        assert _wrap_text(text, max_len=len(text)) == [text]


class TestShortenPrefix:
    def test_no_change_under_limit(self):
        assert _shorten_prefix("AP Living", max_words=2) == "AP Living"

    def test_shortens_long_names(self):
        assert _shorten_prefix("AP Living Room Extended", max_words=2) == "AP Living..."

    def test_single_word(self):
        assert _shorten_prefix("Switch", max_words=2) == "Switch"


class TestLabelMetrics:
    def test_empty_lines(self):
        width, height = _label_metrics([], font_size=12)
        assert width == 12
        assert height == 6

    def test_single_line(self):
        width, height = _label_metrics(["Test"], font_size=12)
        assert width > 12
        assert height > 6

    def test_multiple_lines_increase_height(self):
        _, height1 = _label_metrics(["A"], font_size=12)
        _, height2 = _label_metrics(["A", "B"], font_size=12)
        assert height2 > height1

    def test_longer_text_increases_width(self):
        width1, _ = _label_metrics(["A"], font_size=12)
        width2, _ = _label_metrics(["AAAAAAAAAA"], font_size=12)
        assert width2 > width1
