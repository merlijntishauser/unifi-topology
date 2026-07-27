"""The bundled UniFi icon set must be complete, self-contained and licensed."""

from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

from unifi_topology.render.svg_icons import (
    _ICON_FILES_ISOMETRIC,
    _ICON_FILES_UNIFI,
    _ICON_SETS,
    _icon_base_path,
    _load_isometric_icons,
)

_DIR = pathlib.Path(_icon_base_path()) / "icons-unifi"
_NODE_ICONS = sorted(set(_ICON_FILES_UNIFI.values()))


def _load_normalizer():
    """Load the build script that defines the size invariant, by path.

    It lives in scripts/ rather than the shipped package, so it is loaded
    directly instead of widening the project's import or type-check paths.
    """
    path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "normalize_icon_viewbox.py"
    spec = importlib.util.spec_from_file_location("normalize_icon_viewbox", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_NORMALIZER = _load_normalizer()


def _markup(name: str) -> str:
    return (_DIR / name).read_text(encoding="utf-8")


def test_the_set_is_registered():
    assert "unifi" in _ICON_SETS


def test_every_node_type_is_covered():
    assert set(_ICON_FILES_UNIFI) == set(_ICON_FILES_ISOMETRIC)


def test_every_node_type_has_its_own_icon():
    files = list(_ICON_FILES_UNIFI.values())
    assert len(set(files)) == len(files)


def test_all_referenced_files_exist():
    assert [name for name in _NODE_ICONS if not (_DIR / name).exists()] == []


def test_icons_load_through_the_public_loader():
    icons = _load_isometric_icons("unifi", "#5A6878", None)
    assert set(icons) == set(_ICON_FILES_UNIFI)
    assert all(uri.startswith("data:image/svg+xml;base64,") for uri in icons.values())


# These four live in the isopacks directory but are recoloured copies of this
# set's own artwork (scripts/recolour_icons.py), because isopacks covers none of
# those subjects. They share geometry with icons-unifi by construction.
_RECOLOURED_INTO_ISOPACKS = frozenset(
    {"camera.svg", "speaker.svg", "gameconsole.svg", "sensor.svg"}
)


def test_no_isopacks_geometry_is_reused():
    """The set is licensed as original work; shared path data would undermine that."""
    isometric = pathlib.Path(_icon_base_path()) / "isometric"

    def shapes(directory: pathlib.Path, skip: frozenset[str] = frozenset()) -> set[str]:
        found: set[str] = set()
        for path in directory.glob("*.svg"):
            if path.name in skip:
                continue
            text = path.read_text(encoding="utf-8")
            for raw in re.findall(r'(?:\sd|points)="([^"]{40,})"', text):
                found.add(re.sub(r"\s+", " ", raw).strip())
        return found

    assert shapes(_DIR) & shapes(isometric, skip=_RECOLOURED_INTO_ISOPACKS) == set()


# Filenames that must stay byte-identical: the node-type map and the isopacks
# inventory reach the same artwork under two names.
_ALIASES = [
    ("nas.svg", "storage.svg"),
    ("switch.svg", "switch-module.svg"),
    ("gateway.svg", "router.svg"),
    ("iot.svg", "sensor.svg"),
    ("client.svg", "laptop.svg"),
    ("phone.svg", "mobiledevice.svg"),
    ("other.svg", "cube.svg"),
    ("game_console.svg", "gameconsole.svg"),
]


@pytest.mark.parametrize(("primary", "alias"), _ALIASES)
def test_alias_files_stay_in_sync(primary: str, alias: str):
    """Updating one name and not the other silently splits the set in two."""
    assert _markup(primary) == _markup(alias)


def test_the_set_ships_a_license():
    license_text = (_DIR / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "Ubiquiti" in license_text, "trademark disclaimer must be present"


@pytest.mark.parametrize("name", _NODE_ICONS)
def test_icons_are_self_contained(name: str):
    """These are inlined as data URIs, so external or scripted content cannot work."""
    markup = _markup(name)
    for banned in ("<script", "<style", "xlink:href", "<image", "<foreignObject"):
        assert banned not in markup, f"{name} contains {banned}"
    assert "http://www.w3.org/2000/svg" in markup


@pytest.mark.parametrize("name", _NODE_ICONS)
def test_icons_use_a_square_viewbox(name: str):
    match = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', _markup(name))
    assert match, f"{name} has no parsable viewBox"
    width, height = float(match.group(3)), float(match.group(4))
    assert width == pytest.approx(height), f"{name} viewBox is not square"


@pytest.mark.parametrize("name", _NODE_ICONS)
def test_icons_fill_their_frame_consistently(name: str):
    """Uneven fill makes some devices render as specks; see normalize_icon_viewbox."""
    target = _NORMALIZER.TARGET_FILL
    root = _NORMALIZER._parse_svg(_markup(name))
    min_x, min_y, max_x, max_y = _NORMALIZER._artwork_bounds(root)
    view_width = float(root.get("viewBox", "0 0 1 1").split()[2])
    fill = max(max_x - min_x, max_y - min_y) / view_width
    assert fill == pytest.approx(target, abs=0.02), (
        f"{name} fills {fill:.0%} of its viewBox, expected {target:.0%}"
    )
