"""Private helpers for orthogonal SVG node data attributes."""

from __future__ import annotations

from html import escape as _escape_html


def _base_node_attrs(
    name: str,
    node_type: str,
    group_name: str | None,
) -> dict[str, str]:
    attrs: dict[str, str] = {
        "class": "unm-node",
        "data-node-id": name,
        "data-node-type": node_type,
    }
    if group_name:
        attrs["data-group"] = group_name
    return attrs


def _merge_node_attrs(
    attrs: dict[str, str],
    extra: dict[str, str],
) -> dict[str, str]:
    merged = dict(attrs)
    for key, value in extra.items():
        if key == "class":
            merged["class"] = f"{merged['class']} {value}".strip()
        else:
            merged[key] = value
    return merged


def _render_node_attrs(attrs: dict[str, str]) -> str:
    return "".join(f' {key}="{_escape_html(value, quote=True)}"' for key, value in attrs.items())


def _svg_node_group_attrs(
    node_data: dict[str, dict[str, str]] | None,
    name: str,
    node_type: str,
    group_name: str | None = None,
) -> str:
    attrs = _base_node_attrs(name, node_type, group_name)
    if node_data and (extra := node_data.get(name)):
        attrs = _merge_node_attrs(attrs, extra)
    return _render_node_attrs(attrs)
