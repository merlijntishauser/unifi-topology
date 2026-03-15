"""Tests for generic SVG text layout helpers."""

from __future__ import annotations

from unifi_topology.render.svg_labels import _label_metrics, _shorten_prefix, _wrap_text


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
