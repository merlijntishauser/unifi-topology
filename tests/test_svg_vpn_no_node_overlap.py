"""The orthogonal VPN overlay box must not overlap topology nodes."""

from __future__ import annotations

import re

from tests.svg_vpn_render_helpers import gateway_edges, gateway_node_types, vpn_tunnel
from unifi_topology.render.svg import render_svg


def _rects(block: str) -> list[tuple[float, float, float, float]]:
    rects = []
    for match in re.finditer(
        r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"', block
    ):
        x, y, w, h = (float(g) for g in match.groups())
        rects.append((x, y, w, h))
    return rects


def test_vpn_box_below_all_nodes():
    output = render_svg(
        gateway_edges(),
        node_types=gateway_node_types(),
        vpn_tunnels=[vpn_tunnel()],
    )
    split = output.index('class="vpn-tunnels"')
    node_rects = _rects(output[:split])
    vpn_rect = _rects(output[split:])[0]
    vpn_top = vpn_rect[1]
    assert node_rects
    for _x, y, _w, h in node_rects:
        assert y + h <= vpn_top, f"node rect (y={y}, h={h}) overlaps VPN box top {vpn_top}"
