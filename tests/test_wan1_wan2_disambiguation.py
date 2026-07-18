"""WAN1 must not resolve to a port assigned to WAN2."""

from __future__ import annotations

from unifi_topology.model.topology import PortInfo
from unifi_topology.model.wan import _find_wan1_port, _find_wan2_port


def _port(idx: int, conf_id: str | None) -> PortInfo:
    return PortInfo(
        port_idx=idx,
        name=f"Port {idx}",
        ifname=f"eth{idx}",
        speed=1000,
        aggregation_group=None,
        port_poe=False,
        poe_enable=False,
        poe_good=False,
        poe_power=None,
        wan_networkconf_id=conf_id,
    )


def test_wan1_does_not_match_wan2_assignment():
    # Only a WAN2-assigned port exists, on an index that is not the WAN1 fallback.
    port_table = [_port(9, "WAN2")]
    assert _find_wan1_port(port_table) is None
    wan2 = _find_wan2_port(port_table)
    assert wan2 is not None
    assert wan2.port_idx == 9
