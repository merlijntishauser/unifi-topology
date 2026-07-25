"""Give every icon in a set the same optical size by retargeting its viewBox.

The isometric renderer drops each icon into a square box with
``preserveAspectRatio="xMidYMid meet"``, so an icon that leaves more empty
margin inside its own viewBox simply draws smaller on the tile. Measured against
the bundled isopacks art (which fills 82-97% of its viewBox), the UniFi set
filled only 58-90%, so sensors and phones shrank to specks on the diagram.

This rewrites only the root ``viewBox``/``width``/``height`` so that every icon's
artwork -- including its stroke and ground shadow -- fills ``TARGET_FILL`` of a
square frame. No geometry is touched, so the change is reversible and the
artwork stays byte-identical.

Usage:
    python scripts/normalize_icon_viewbox.py src/unifi_topology/assets/icons/icons-unifi
"""

from __future__ import annotations

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"

# Fraction of the square frame the artwork should span on its dominant axis.
# The bundled isopacks icons average 0.895; staying just under keeps a hairline
# of margin so strokes are never clipped by the viewport.
TARGET_FILL = 0.88

_TRANSLATE = re.compile(r"translate\(\s*([-\d.]+)[\s,]+([-\d.]+)\s*\)")
_SCALE = re.compile(r"scale\(\s*([-\d.]+)\s*\)")
_ROOT_ATTR = re.compile(r"^(<svg\b[^>]*?)/?>", re.DOTALL)


class EmptyIconError(ValueError):
    """Raised when an icon contains no measurable geometry."""


def _parse_svg(markup: str) -> ET.Element:
    """Parse an icon, refusing doctypes so stdlib entity expansion cannot bite.

    These files are repo-controlled, but the parser is not hardened against XXE
    or entity expansion, and icon packs arrive from outside the repo. Our icons
    carry no DTD, so rejecting one outright is free.
    """
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", markup, re.IGNORECASE):
        raise ValueError("icon declares a DTD or entity; refusing to parse")
    return ET.fromstring(markup)  # noqa: S314 - guarded above


def _stroke_pad(element: ET.Element) -> float:
    """Half the stroke width, which is how far a stroke bleeds past the edge."""
    if not element.get("stroke") or element.get("stroke") == "none":
        return 0.0
    return float(element.get("stroke-width", "1")) / 2.0


def _polygon_bounds(element: ET.Element) -> tuple[float, float, float, float]:
    coords = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", element.get("points", ""))]
    xs, ys = coords[0::2], coords[1::2]
    pad = _stroke_pad(element)
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def _circle_bounds(element: ET.Element) -> tuple[float, float, float, float]:
    cx = float(element.get("cx", "0"))
    cy = float(element.get("cy", "0"))
    radius = float(element.get("r", "0")) + _stroke_pad(element)
    return cx - radius, cy - radius, cx + radius, cy + radius


def _shape_bounds(element: ET.Element) -> tuple[float, float, float, float] | None:
    if element.tag == f"{SVG_NS}polygon" and element.get("points"):
        return _polygon_bounds(element)
    if element.tag == f"{SVG_NS}circle":
        return _circle_bounds(element)
    return None


def _group_transform(root: ET.Element) -> tuple[float, float, float]:
    """Return (tx, ty, scale) from the single wrapping group, if there is one."""
    group = root.find(f"{SVG_NS}g")
    transform = group.get("transform", "") if group is not None else ""
    translate = _TRANSLATE.search(transform)
    scale = _SCALE.search(transform)
    tx, ty = (float(translate.group(1)), float(translate.group(2))) if translate else (0.0, 0.0)
    return tx, ty, float(scale.group(1)) if scale else 1.0


def _artwork_bounds(root: ET.Element) -> tuple[float, float, float, float]:
    """Union of every shape's bounds, in the root's own user units."""
    boxes = [box for element in root.iter() if (box := _shape_bounds(element)) is not None]
    if not boxes:
        raise EmptyIconError("no polygon or circle geometry found")
    tx, ty, scale = _group_transform(root)
    min_x = min(b[0] for b in boxes) * scale + tx
    min_y = min(b[1] for b in boxes) * scale + ty
    max_x = max(b[2] for b in boxes) * scale + tx
    max_y = max(b[3] for b in boxes) * scale + ty
    return min_x, min_y, max_x, max_y


def _square_frame(bounds: tuple[float, float, float, float]) -> tuple[float, float, float]:
    """A square viewBox centred on the artwork, sized so it fills TARGET_FILL."""
    min_x, min_y, max_x, max_y = bounds
    side = max(max_x - min_x, max_y - min_y) / TARGET_FILL
    centre_x = (min_x + max_x) / 2
    centre_y = (min_y + max_y) / 2
    return centre_x - side / 2, centre_y - side / 2, side


def _rewrite_root(markup: str, origin_x: float, origin_y: float, side: float) -> str:
    """Replace the root element's viewBox and intrinsic size, leaving art untouched."""
    match = _ROOT_ATTR.match(markup)
    if match is None:
        raise ValueError("no root <svg> element")
    head = match.group(1)
    head = re.sub(r'\s(viewBox|width|height)="[^"]*"', "", head)
    view_box = f"{origin_x:.2f} {origin_y:.2f} {side:.2f} {side:.2f}"
    head = f'{head} viewBox="{view_box}" width="{side:.2f}" height="{side:.2f}"'
    return head + ">" + markup[match.end() :]


def normalize(path: pathlib.Path) -> float:
    """Retarget one icon's viewBox. Returns the fill fraction it had before."""
    markup = path.read_text(encoding="utf-8")
    root = _parse_svg(markup)
    bounds = _artwork_bounds(root)
    previous = [float(n) for n in root.get("viewBox", "0 0 1 1").split()]
    before = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) / max(previous[2], previous[3])
    origin_x, origin_y, side = _square_frame(bounds)
    path.write_text(_rewrite_root(markup, origin_x, origin_y, side), encoding="utf-8")
    return before


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    directory = pathlib.Path(sys.argv[1])
    files = sorted(directory.glob("*.svg"))
    if not files:
        print(f"no SVGs in {directory}")
        return 1
    fills = {path.name: normalize(path) for path in files}
    for name, fill in sorted(fills.items(), key=lambda item: item[1]):
        print(f"  {name:24} {fill * 100:5.1f}% -> {TARGET_FILL * 100:.0f}%")
    print(f"\n{len(files)} icons; mean fill was {sum(fills.values()) / len(fills) * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
