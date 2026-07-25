"""Generate placeholder isometric device icons for types isopacks does not cover.

NOTE: these are primitive-built stand-ins, visibly simpler than the hand-drawn
isopacks art they sit beside (which uses near-white bodies, rounded forms and
small colour accents). They are informative but not final; replace them with
proper art when available. printer.svg now comes from upstream isopacks.

True 30-degree isometric projection, three-tone blue-grey faces with a dark
outline and a soft ground shadow, matching the palette sampled from the
existing icon set (#231F20 outline, #6885A9 / #B2CBED / #D6E2F2 faces).
"""

import math
import pathlib

C = math.cos(math.radians(30))
S = math.sin(math.radians(30))

OUTLINE = "#231F20"
TOP = "#DCE9F9"
LEFT = "#A8BFDC"
RIGHT = "#6885A9"
DARK = "#365E7F"
GLASS = "#EAF4FF"
ACCENT = "#4B6E98"
SHADOW = "#231F20"
STROKE_W = 3.0


def project(p):
    x, y, z = p
    return ((x - y) * C, (x + y) * S - z)


def poly(points, fill, stroke=OUTLINE, width=STROKE_W, opacity=None):
    pts = " ".join(f"{px:.2f},{py:.2f}" for px, py in (project(p) for p in points))
    op = f' opacity="{opacity}"' if opacity is not None else ""
    st = f' stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"' if stroke else ""
    return f'<polygon points="{pts}" fill="{fill}"{st}{op}/>'


def box(x0, y0, z0, x1, y1, z1, top=TOP, left=LEFT, right=RIGHT, stroke=OUTLINE):
    """Emit the three visible faces of an axis-aligned box, painter-ordered."""
    faces = [
        ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], left),
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], right),
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top),
    ]
    return "".join(poly(pts, fill, stroke=stroke) for pts, fill in faces)


def disc_on_right(x, cy, cz, r, fill, stroke=OUTLINE, n=28, width=STROKE_W):
    """A circle lying on the x = const face, sampled as a polygon."""
    pts = [
        (x, cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]
    return poly(pts, fill, stroke=stroke, width=width)


def disc_on_top(cx, cy, z, r, fill, stroke=OUTLINE, n=28, width=STROKE_W):
    pts = [
        (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z)
        for i in range(n)
    ]
    return poly(pts, fill, stroke=stroke, width=width)


def ground_shadow(x0, y0, x1, y1, spread=0.16):
    """Soft contact shadow on the ground plane, offset toward the light."""
    dx, dy = (x1 - x0) * spread, (y1 - y0) * spread
    pts = [
        (x0 + dx, y0 + dy, 0),
        (x1 + dx * 2.2, y0 + dy, 0),
        (x1 + dx * 2.2, y1 + dy * 2.2, 0),
        (x0 + dx, y1 + dy * 2.2, 0),
    ]
    body = poly(pts, SHADOW, stroke=None, opacity=0.22)
    return f'<g filter="url(#soft)">{body}</g>'


def wrap(body, pad=9):
    """Compute the bounding box from the emitted geometry and frame it."""
    import re

    nums = [
        tuple(map(float, pair.split(",")))
        for chunk in re.findall(r'points="([^"]+)"', body)
        for pair in chunk.split()
    ]
    xs = [p[0] for p in nums]
    ys = [p[1] for p in nums]
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad
    w, h = maxx - minx, maxy - miny
    defs = (
        '<defs><filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="4"/></filter></defs>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.1f} {miny:.1f} '
        f'{w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}">{defs}{body}</svg>'
    )


def camera():
    """Bullet camera: body box on a short mount, lens on the front-right face."""
    s = ground_shadow(-34, -30, 40, 30)
    s += box(-16, -12, 0, 4, 12, 14, top="#B5C5DC", left="#93A9C4", right="#5C7794")  # mount
    s += box(-30, -26, 14, 34, 26, 56)  # body
    s += disc_on_right(34.6, 0, 35, 17, DARK)  # lens housing
    s += disc_on_right(35.4, 0, 35, 10, "#1B2733", stroke=None)  # glass
    s += disc_on_right(36.0, -4, 40, 3.4, GLASS, stroke=None)  # catchlight
    return s


def speaker():
    """Tall cabinet with a woofer and tweeter on the front-right face."""
    s = ground_shadow(-24, -22, 26, 22)
    s += box(-22, -20, 0, 24, 20, 76)
    s += disc_on_right(24.6, 0, 24, 13, DARK)
    s += disc_on_right(25.2, 0, 24, 7, "#1B2733", stroke=None)
    s += disc_on_right(24.6, 0, 55, 6.5, DARK)
    s += disc_on_right(25.2, 0, 55, 3.2, "#1B2733", stroke=None)
    return s


def game_console():
    """Low, wide console with a lighter top panel and a power LED."""
    s = ground_shadow(-42, -30, 42, 30)
    s += box(-40, -28, 0, 40, 28, 18)  # base
    s += box(-34, -23, 18, 34, 23, 24, top=GLASS, left="#A8BFDC", right="#6885A9")  # top panel
    s += disc_on_top(22, 0, 24.4, 4.2, ACCENT, width=2.0)  # power ring
    s += poly(  # front vent
        [(40.2, -18, 5), (40.2, 14, 5), (40.2, 14, 10), (40.2, -18, 10)],
        "#1B2733",
        width=2.0,
    )
    return s


def iot():
    """Small sensor cube with a stub antenna and a status LED."""
    s = ground_shadow(-20, -18, 22, 18)
    s += box(-18, -16, 0, 20, 16, 30)
    s += poly(  # antenna mast
        [(12, -2, 30), (16, -2, 30), (16, -2, 56), (12, -2, 56)],
        "#5C7794",
        width=2.0,
    )
    s += disc_on_top(14, -2, 57, 5.0, ACCENT, width=2.0)
    s += disc_on_right(20.4, -6, 18, 4.0, "#7FD4A0", width=2.0)  # status LED
    return s


ICONS = {
    "camera": camera,
    "speaker": speaker,
    "gameconsole": game_console,
    "sensor": iot,
}

if __name__ == "__main__":
    out = pathlib.Path("src/unifi_topology/assets/icons/isometric")
    for name, fn in ICONS.items():
        svg = wrap(fn())
        (out / f"{name}.svg").write_text(svg)
        print(f"{name:14} {len(svg):>6} bytes")
