"""Icon loading and color management for SVG rendering."""

from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path

from .svg_theme import SvgTheme

# Icon file mappings per icon set
# Isometric set uses existing icons from root and isometric/ directories
# New device types fall back to generic icons in isometric set
_ICON_FILES_ISOMETRIC = {
    "gateway": "router-network.svg",
    "switch": "server-network.svg",
    "ap": "access-point.svg",
    "camera": "laptop.svg",
    "tv": "laptop.svg",
    "phone": "laptop.svg",
    "printer": "laptop.svg",
    "nas": "server.svg",
    "speaker": "laptop.svg",
    "game_console": "laptop.svg",
    "iot": "server.svg",
    "client": "laptop.svg",
    "client_cluster": "laptop.svg",
    "other": "server.svg",
}

_ISO_ICON_FILES_ISOMETRIC = {
    "gateway": "router.svg",
    "switch": "switch-module.svg",
    "ap": "tower.svg",
    "camera": "laptop.svg",
    "tv": "laptop.svg",
    "phone": "laptop.svg",
    "printer": "laptop.svg",
    "nas": "server.svg",
    "speaker": "laptop.svg",
    "game_console": "laptop.svg",
    "iot": "server.svg",
    "client": "laptop.svg",
    "client_cluster": "laptop.svg",
    "other": "server.svg",
}

# Modern set uses consistent naming in modern/ directory
_ICON_FILES_MODERN = {
    "gateway": "gateway.svg",
    "switch": "switch.svg",
    "ap": "ap.svg",
    "camera": "camera.svg",
    "tv": "tv.svg",
    "phone": "phone.svg",
    "printer": "printer.svg",
    "nas": "nas.svg",
    "speaker": "speaker.svg",
    "game_console": "game_console.svg",
    "iot": "iot.svg",
    "client": "client.svg",
    "client_cluster": "client.svg",
    "other": "other.svg",
}

# Icon set registry: maps set names to (flat_dir, iso_dir, flat_files, iso_files)
_ICON_SETS = {
    "isometric": (
        "",  # Flat icons in root icons/ directory
        "isometric",  # Isometric icons in isometric/ subdirectory
        _ICON_FILES_ISOMETRIC,
        _ISO_ICON_FILES_ISOMETRIC,
    ),
    "modern": (
        "modern-flat",  # Flat icons for orthogonal SVG
        "modern",  # Isometric icons for iso SVG
        _ICON_FILES_MODERN,
        _ICON_FILES_MODERN,
    ),
}

# Node type fill/stroke colors for orthogonal rendering
_TYPE_COLORS = {
    "gateway": ("#ffd199", "#f08a00"),
    "switch": ("#bfe4ff", "#1c6dd0"),
    "ap": ("#c4f2d4", "#1f9a50"),
    "camera": ("#b3e5fc", "#0277bd"),
    "tv": ("#d1c4e9", "#512da8"),
    "phone": ("#c8e6c9", "#388e3c"),
    "printer": ("#cfd8dc", "#546e7a"),
    "nas": ("#ffe0b2", "#e65100"),
    "speaker": ("#b2dfdb", "#00796b"),
    "game_console": ("#e1bee7", "#7b1fa2"),
    "iot": ("#b2ebf2", "#00838f"),
    "client": ("#e4ccff", "#6b2fb4"),
    "client_cluster": ("#d4b8ff", "#5a25a0"),
    "other": ("#e3e3e3", "#7b7b7b"),
}


def _safe_node_type(node_type: str) -> str:
    """Restrict a node type to the known set so it is safe to interpolate."""
    return node_type if node_type in _TYPE_COLORS else "other"


# Type ordering for layout sorting
_TYPE_ORDER = [
    "gateway",
    "switch",
    "ap",
    "camera",
    "tv",
    "phone",
    "printer",
    "nas",
    "speaker",
    "game_console",
    "iot",
    "client",
    "client_cluster",
    "other",
]


def _darken_hex(color: str, factor: float = 0.35) -> str:
    """Darken a hex color by *factor* (0..1). Returns 6-digit hex."""
    c = color.lstrip("#")
    if len(c) != 6:
        return color
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    m = 1.0 - factor
    return f"#{int(r * m):02x}{int(g * m):02x}{int(b * m):02x}"


def _build_decal_colors(theme: SvgTheme, factor: float = 0.35) -> dict[str, str]:
    """Derive per-type icon decal colors by darkening each node's gradient end."""
    node_attrs = {
        "gateway": theme.node_gateway,
        "switch": theme.node_switch,
        "ap": theme.node_ap,
        "client": theme.node_client,
        "other": theme.node_other,
        "camera": theme.node_camera,
        "tv": theme.node_tv,
        "phone": theme.node_phone,
        "printer": theme.node_printer,
        "nas": theme.node_nas,
        "speaker": theme.node_speaker,
        "game_console": theme.node_game_console,
        "iot": theme.node_iot,
        "client_cluster": theme.node_client_cluster,
    }
    return {name: _darken_hex(pair[1], factor) for name, pair in node_attrs.items()}


def _icon_base_path() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "icons"


def _icon_set_config(
    icon_set: str,
) -> tuple[str, str, dict[str, str], dict[str, str]]:
    return _ICON_SETS.get(icon_set, _ICON_SETS["isometric"])


def _icon_path(base: Path, subdir: str, filename: str) -> Path:
    return base / subdir / filename if subdir else base / filename


def _svg_data_uri(data: bytes) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _load_icon_text(path: Path, *, decal_color: str) -> str | None:
    if not path.exists():
        return None
    data = path.read_text(encoding="utf-8").replace("#DECAL0", decal_color).encode("utf-8")
    return _svg_data_uri(data)


def _load_icon_bytes(path: Path) -> str | None:
    if not path.exists():
        return None
    return _svg_data_uri(path.read_bytes())


def _load_primary_icon(path: Path, *, decal_color: str | None) -> str | None:
    if decal_color is None:
        return _load_icon_bytes(path)
    return _load_icon_text(path, decal_color=decal_color)


def _node_icon_uri(
    node_type: str,
    *,
    base: Path,
    primary_subdir: str,
    primary_files: dict[str, str],
    fallback_subdir: str,
    fallback_files: dict[str, str],
    decal_color: str | None,
) -> str | None:
    filename = primary_files.get(node_type)
    if filename:
        primary_path = _icon_path(base, primary_subdir, filename)
        if icon := _load_primary_icon(primary_path, decal_color=decal_color):
            return icon
    fallback_filename = fallback_files.get(node_type)
    if fallback_filename:
        fallback_path = _icon_path(base, fallback_subdir, fallback_filename)
        return _load_icon_bytes(fallback_path)
    return None


def _load_icon_map(
    node_types: list[str],
    *,
    base: Path,
    primary_subdir: str,
    primary_files: dict[str, str],
    fallback_subdir: str,
    fallback_files: dict[str, str],
    decal_color_for_type: Callable[[str], str | None],
) -> dict[str, str]:
    icons: dict[str, str] = {}
    for node_type in node_types:
        icon = _node_icon_uri(
            node_type,
            base=base,
            primary_subdir=primary_subdir,
            primary_files=primary_files,
            fallback_subdir=fallback_subdir,
            fallback_files=fallback_files,
            decal_color=decal_color_for_type(node_type),
        )
        if icon is not None:
            icons[node_type] = icon
    return icons


def _load_icons(icon_set: str = "isometric", decal_color: str = "#1a1a1a") -> dict[str, str]:
    """Load flat (non-isometric) icons for the specified icon set.

    Falls back to isometric icons if the requested icon is not found in the set.
    Modern icons use #DECAL0 as placeholder which gets replaced with decal_color.
    """
    base = _icon_base_path()
    subdir, _, file_map, _ = _icon_set_config(icon_set)
    fallback_subdir, _, fallback_files, _ = _ICON_SETS["isometric"]
    return _load_icon_map(
        list(_ICON_FILES_ISOMETRIC.keys()),
        base=base,
        primary_subdir=subdir,
        primary_files=file_map,
        fallback_subdir=fallback_subdir,
        fallback_files=fallback_files,
        decal_color_for_type=lambda _node_type: decal_color,
    )


def _load_isometric_icons(
    icon_set: str = "isometric",
    decal_color: str = "#5A6878",
    decal_colors: dict[str, str] | None = None,
) -> dict[str, str]:
    """Load isometric icons for the specified icon set.

    Falls back to isometric icons if the requested icon is not found in the set.
    Modern icons use #DECAL0 as placeholder which gets replaced with a per-type
    color from *decal_colors* (falling back to *decal_color*).
    """
    base = _icon_base_path()
    _, iso_subdir, _, iso_file_map = _icon_set_config(icon_set)
    _, fallback_iso_subdir, _, fallback_iso_files = _ICON_SETS["isometric"]
    return _load_icon_map(
        list(_ISO_ICON_FILES_ISOMETRIC.keys()),
        base=base,
        primary_subdir=iso_subdir,
        primary_files=iso_file_map,
        fallback_subdir=fallback_iso_subdir,
        fallback_files=fallback_iso_files,
        decal_color_for_type=lambda node_type: (
            decal_colors.get(node_type, decal_color) if decal_colors else decal_color
        ),
    )
