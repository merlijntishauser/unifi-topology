"""Render an example SVG from the live controller, anonymized for publication.

The real topology carries hardware MACs, vendor OUIs, room names and household
members' first names. This keeps the real *shape* of the network -- device count,
port fan-out, client distribution -- while replacing every identifier.
"""

import dataclasses
import pathlib
import re
import sys

from unifi_topology import (
    Config,
    build_client_edges,
    build_node_type_map,
    fetch_clients,
    fetch_devices,
    normalize_devices,
    render_svg_isometric,
)
from unifi_topology.model.edges import build_edges
from unifi_topology.render.svg_theme import DEFAULT_THEME, SvgOptions

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
ENV = sys.argv[2] if len(sys.argv) > 2 else ".env"

LABELS = {
    "gateway": "Gateway",
    "switch": "Switch",
    "ap": "Access Point",
    "camera": "Camera",
    "tv": "TV",
    "phone": "Phone",
    "printer": "Printer",
    "nas": "NAS",
    "speaker": "Speaker",
    "game_console": "Console",
    "iot": "Sensor",
    "client": "Client",
    "client_cluster": "Clients",
    "other": "Device",
}


def synthetic_mac(index: int) -> str:
    """A locally-administered MAC (02:...), which no real vendor can own."""
    return f"02:00:00:{index >> 16 & 0xFF:02x}:{index >> 8 & 0xFF:02x}:{index & 0xFF:02x}"


config = Config.from_env(env_file=ENV)
devices = normalize_devices(fetch_devices(config))
clients = fetch_clients(config)

index = {d.mac: d.name for d in devices}
edges = build_edges(devices, include_ports=True, only_unifi=False)
edges += build_client_edges(clients, index)
types = build_node_type_map(devices, clients, client_mode="all")

# Stable order so the output is reproducible run to run.
nodes = sorted({e.left for e in edges} | {e.right for e in edges} | set(types))
mac_map = {mac: synthetic_mac(i) for i, mac in enumerate(nodes)}

counters: dict[str, int] = {}
anon_names: dict[str, str] = {}
for mac in nodes:
    kind = types.get(mac, "other")
    counters[kind] = counters.get(kind, 0) + 1
    anon_names[mac_map[mac]] = f"{LABELS.get(kind, 'Device')} {counters[kind]}"


def anon_label(label: str | None) -> str | None:
    """Edge labels read '<device name>: Port N'; keep the port, drop the name."""
    if not label:
        return label
    return re.sub(r"^[^:]*:\s*", "", label) or None


anon_types = {mac_map[m]: t for m, t in types.items()}
# replace() keeps poe/wireless/speed/vlans, which all affect how the edge draws.
anon_edges = [
    dataclasses.replace(e, left=mac_map[e.left], right=mac_map[e.right], label=anon_label(e.label))
    for e in edges
]

print(f"{len(devices)} devices, {len(clients)} clients -> {len(nodes)} anonymized nodes")

VARIANTS = {
    "tree-isopacks": (SvgOptions(), "isometric"),
    "compact-unifi": (SvgOptions(iso_lighting=True, iso_compact_layout=True), "unifi"),
}
for label, (options, icon_set) in VARIANTS.items():
    theme = dataclasses.replace(DEFAULT_THEME, icon_set=icon_set)
    svg = render_svg_isometric(
        anon_edges, node_types=anon_types, node_names=anon_names, options=options, theme=theme
    )
    path = OUT / f"topology-{label}.svg"
    path.write_text(svg, encoding="utf-8")
    print(f"  {label:7} {len(svg):>9,} bytes -> {path.name}")
