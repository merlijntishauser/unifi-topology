"""Text formatting and label utilities for SVG rendering."""

from __future__ import annotations

import re
from html import escape as _escape_html

from . import _svg_edge_labels, _svg_gateway_labels

__all__ = [
    "_build_dual_wan_label_lines",
    "_build_single_wan_label_lines",
    "_build_vpn_label_lines",
    "_build_wan_label_lines",
    "_compact_edge_label",
    "_escape_attr",
    "_escape_text",
    "_extract_device_name",
    "_extract_port_text",
    "_format_compact_ports",
    "_format_port_label_lines",
    "_format_wan_interface_line",
    "_format_wan_speed",
    "_format_wan_speed_line",
    "_label_metrics",
    "_shorten_prefix",
    "_strip_local_port",
    "_wrap_text",
]


# Characters illegal in any well-formed XML 1.0 document. Unlike the reserved
# entities, these cannot be encoded by a character reference and must be removed
# before serialization or the entire SVG becomes unparseable. The allowed
# control characters #x9 (tab), #xA (newline) and #xD (carriage return) are
# deliberately excluded from this set.
_XML_INVALID = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def _strip_xml_invalid(value: str) -> str:
    """Remove characters that cannot appear in a well-formed XML document."""
    return _XML_INVALID.sub("", value)


def _escape_text(value: str) -> str:
    """Escape a string for use as XML text content (e.g. inside <text>/<tspan>)."""
    cleaned = _strip_xml_invalid(value)
    return cleaned.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(value: str) -> str:
    """Escape a string for use as an XML attribute value (e.g. data-node-id)."""
    return _escape_html(_strip_xml_invalid(value), quote=True)


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
