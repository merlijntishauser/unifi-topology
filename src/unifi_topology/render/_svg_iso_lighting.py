"""Light model and contact shadows for isometric node rendering.

The default isometric look shades the two visible side faces with flat theme
greys, which reads as tilted flat art rather than solid objects in a space.
This module derives all three visible faces from a single light direction so a
node's sides relate to its own colour, and provides the contact shadow that
seats a node on the floor plane.
"""

from __future__ import annotations

from ._svg_node_types import _safe_node_type
from .svg_theme import SvgTheme, node_type_gradients

# Relative luminance of the two shaded faces for a light source above and to the
# upper-left: the left face is angled away, the right face furthest away and so
# reads darkest. The top face is not listed because it is not shaded here -- it
# keeps the node's own themed fill, which is what the sides are derived against.
_FACE_LEFT = 0.76
_FACE_RIGHT = 0.55

# Contact shadow: offset along the light direction (down-right), scaled by the
# node's extrusion so taller nodes cast a longer shadow.
_SHADOW_DX = 0.16
_SHADOW_DY = 0.10
_SHADOW_OPACITY = 0.28


def _hex_to_rgb(color: str) -> tuple[int, int, int] | None:
    value = color.lstrip("#")
    if len(value) != 6:
        return None
    try:
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
    except ValueError:
        return None


def _shade(color: str, factor: float) -> str:
    """Scale a hex colour's channels by *factor*, clamped to the 0-255 range."""
    rgb = _hex_to_rgb(color)
    if rgb is None:
        return color
    scaled = tuple(max(0, min(255, round(channel * factor))) for channel in rgb)
    return f"#{scaled[0]:02x}{scaled[1]:02x}{scaled[2]:02x}"


def iso_face_colors(node_type: str, theme: SvgTheme) -> tuple[str, str]:
    """Return (left_fill, right_fill) shaded from the node's own themed colour.

    Derived from the same gradient the top face is painted with, so the faces of
    a node agree. Reading a fixed palette here instead left the sides green under
    a theme whose access points are blue.
    """
    base = dict(node_type_gradients(theme))[_safe_node_type(node_type)][0]
    return _shade(base, _FACE_LEFT), _shade(base, _FACE_RIGHT)


def render_contact_shadow(
    lines: list[str],
    *,
    x: float,
    y: float,
    tile_w: float,
    tile_h: float,
    node_depth: float,
    filter_id: str,
) -> None:
    """Draw a soft shadow on the floor plane beneath a node tile.

    The shadow is the tile's diamond footprint, seated at the base of the
    extrusion and pushed along the light direction. Taller nodes throw a
    longer, softer shadow, which is what makes elevation legible.
    """
    lift = node_depth
    offset_x = tile_w * _SHADOW_DX * (0.5 + lift / max(tile_h, 1.0))
    offset_y = tile_h * _SHADOW_DY * (0.5 + lift / max(tile_h, 1.0))
    cx = x + tile_w / 2 + offset_x
    cy = y + tile_h / 2 + lift + offset_y
    points = [
        (cx, cy - tile_h / 2),
        (cx + tile_w / 2, cy),
        (cx, cy + tile_h / 2),
        (cx - tile_w / 2, cy),
    ]
    points_str = " ".join(f"{px},{py}" for px, py in points)
    lines.append(
        f'<polygon class="iso-contact-shadow" points="{points_str}" fill="#000000" '
        f'opacity="{_SHADOW_OPACITY}" filter="url(#{filter_id})"/>'
    )
