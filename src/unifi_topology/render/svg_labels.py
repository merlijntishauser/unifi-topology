"""Text formatting and label utilities for SVG rendering."""

from __future__ import annotations

from . import _svg_edge_labels, _svg_gateway_labels


def _escape_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_extract_port_text = _svg_edge_labels._extract_port_text
_extract_device_name = _svg_edge_labels._extract_device_name
_format_compact_ports = _svg_edge_labels._format_compact_ports
_compact_edge_label = _svg_edge_labels._compact_edge_label
_format_port_label_lines = _svg_edge_labels._format_port_label_lines
_format_wan_speed = _svg_gateway_labels._format_wan_speed
_format_wan_interface_line = _svg_gateway_labels._format_wan_interface_line
_format_wan_speed_line = _svg_gateway_labels._format_wan_speed_line
_build_single_wan_label_lines = _svg_gateway_labels._build_single_wan_label_lines
_build_dual_wan_label_lines = _svg_gateway_labels._build_dual_wan_label_lines
_build_wan_label_lines = _svg_gateway_labels._build_wan_label_lines
_build_vpn_label_lines = _svg_gateway_labels._build_vpn_label_lines


def _strip_local_port(label: str, node_type: str) -> str:
    """Strip the local port from a bidirectional label for single-port devices (APs)."""
    if node_type == "ap" and "<->" in label:
        return label.split("<->", 1)[0].strip()
    return label


def _wrap_text(label: str, *, max_len: int = 24) -> list[str]:
    if len(label) <= max_len:
        return [label]
    split_at = label.rfind(" ", 0, max_len + 1)
    if split_at == -1:
        split_at = max_len
    first = label[:split_at].rstrip()
    rest = label[split_at:].lstrip()
    return [first, rest] if rest else [first]


def _shorten_prefix(name: str, max_words: int = 2) -> str:
    words = name.split()
    if len(words) <= max_words:
        return name
    return " ".join(words[:max_words]) + "..."


def _label_metrics(
    lines: list[str], *, font_size: int, padding_x: int = 6, padding_y: int = 3
) -> tuple[float, float]:
    max_len = max((len(line) for line in lines), default=0)
    text_width = max_len * font_size * 0.6
    text_height = len(lines) * (font_size + 2)
    width = text_width + padding_x * 2
    height = text_height + padding_y * 2
    return width, height
