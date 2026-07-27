"""Restyle icons from the UniFi set into the isopacks blue palette.

isopacks covers no camera, speaker, games console or sensor -- none of the 1062
SVGs in any upstream collection does. Those four node types were filled with
primitive-built stand-ins (7-10 polygons of flat, saturated blue-grey against
isopacks' 10-31 of near-white bodies with rounded forms), which read as a
different library sitting in the same diagram.

The UniFi set draws all four properly. This maps its neutral-grey palette onto
the isopacks blue family so the artwork can be reused there, keeping the forms
and losing the mismatch. Geometry is untouched; only fill and stroke colours
change.

Usage:
    python scripts/recolour_icons.py
"""

from __future__ import annotations

import pathlib

ICONS = pathlib.Path(__file__).resolve().parents[1] / "src/unifi_topology/assets/icons"

# UniFi neutral grey -> isopacks blue. Sampled from router.svg, laptop.svg and
# storage.svg, which are the truest expression of the isopacks house style.
PALETTE = {
    "#24282B": "#231F20",  # outline
    "#15181A": "#231F20",
    "#FAFBFC": "#F0F7FF",  # highlights
    "#F2F4F6": "#F0F7FF",
    "#E9EDF1": "#CDD9EE",  # top faces
    "#DCE1E6": "#CCD8EE",
    "#CBD3DA": "#B2CBED",  # upper sides
    "#A0AAB4": "#B5C5DC",
    "#798187": "#6885A9",  # shaded sides
    "#6F7A85": "#6885A9",
    "#555B60": "#4B6E98",
    "#4A535C": "#4B6E98",
    "#4B5155": "#4B6E98",
    "#42474B": "#365E7F",  # recesses
    "#3B4044": "#365E7F",
    "#373B3F": "#365E7F",
    "#26292C": "#2A4A66",
    "#1C1F22": "#233D55",
}

# Which UniFi file supplies which isopacks filename.
SOURCES = {
    "camera.svg": "camera.svg",
    "speaker.svg": "speaker.svg",
    "gameconsole.svg": "game_console.svg",
    "sensor.svg": "iot.svg",
}


def recolour(markup: str) -> str:
    for grey, blue in PALETTE.items():
        markup = markup.replace(grey, blue).replace(grey.lower(), blue)
    return markup


def main() -> int:
    source_dir = ICONS / "icons-unifi"
    target_dir = ICONS / "isometric"
    if not source_dir.is_dir():
        print(f"missing {source_dir}")
        return 1
    for target, source in sorted(SOURCES.items()):
        markup = recolour((source_dir / source).read_text(encoding="utf-8"))
        (target_dir / target).write_text(markup, encoding="utf-8")
        print(f"  {source:18} -> isometric/{target}  ({len(markup):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
