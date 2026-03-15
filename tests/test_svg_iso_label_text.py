import re

from unifi_topology.model.topology import Edge
from unifi_topology.render.svg_isometric import render_svg_isometric


def test_isometric_port_label_uses_device_name_not_local():
    """Unidirectional port label should show the upstream device name,
    not 'local: Port 5'."""
    output = render_svg_isometric(
        [Edge("Switch TV Kast", "Client", label="Switch TV Kast: Port 5")],
        node_types={"Switch TV Kast": "switch", "Client": "client"},
    )
    tspans = re.findall(r"<tspan[^>]*>([^<]+)</tspan>", output)
    label_text = " ".join(tspans)
    assert "local" not in label_text.lower()
    assert "Switch TV" in label_text


def test_isometric_bidirectional_label_uses_local_for_own_port():
    """Bidirectional port label: first line shows upstream prefix,
    second line shows 'local' for the node's own port."""
    output = render_svg_isometric(
        [Edge("GW", "Switch", label="GW: Port 1 <-> Switch: Port 5")],
        node_types={"GW": "gateway", "Switch": "switch"},
    )
    tspans = re.findall(r"<tspan[^>]*>([^<]+)</tspan>", output)
    label_text = " ".join(tspans)
    assert "GW" in label_text
    assert "local" in label_text.lower()


def test_isometric_ap_drops_local_port():
    """APs have a single port, so the 'local: Port 0' line is redundant
    and should be omitted."""
    output = render_svg_isometric(
        [Edge("Switch", "AP", label="Switch: Port 4 <-> AP: Port 0")],
        node_types={"Switch": "switch", "AP": "ap"},
    )
    tspans = re.findall(r"<tspan[^>]*>([^<]+)</tspan>", output)
    label_text = " ".join(tspans)
    assert "Switch" in label_text
    assert "local" not in label_text.lower()
