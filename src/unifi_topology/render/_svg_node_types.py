"""Node-type constants shared across SVG rendering modules.

A neutral home for the known node types, their colors, and layout ordering, so
that layout, icon, and node-rendering modules do not have to import each other
for these definitions.
"""

from __future__ import annotations

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
