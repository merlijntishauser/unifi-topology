"""Unit tests for firewall models."""

import pytest

from unifi_topology.model.firewall import FirewallGroup, FirewallPolicy, FirewallZone


class TestFirewallZone:
    def test_basic(self):
        zone = FirewallZone(id="z1", name="IoT", network_ids=("n1", "n2"))
        assert zone.id == "z1"
        assert zone.name == "IoT"
        assert zone.network_ids == ("n1", "n2")

    def test_defaults(self):
        zone = FirewallZone(id="z1", name="WAN")
        assert zone.network_ids == ()

    def test_frozen(self):
        zone = FirewallZone(id="z1", name="WAN")
        with pytest.raises(AttributeError):
            zone.name = "LAN"  # type: ignore[misc]


class TestFirewallPolicy:
    def test_basic(self):
        policy = FirewallPolicy(
            id="p1",
            name="Block IoT",
            enabled=True,
            action="BLOCK",
            source_zone_id="z_iot",
            destination_zone_id="z_lan",
        )
        assert policy.action == "BLOCK"
        assert policy.protocol == "all"
        assert policy.port_ranges == ()

    def test_with_ports(self):
        policy = FirewallPolicy(
            id="p1",
            name="Allow DNS",
            enabled=True,
            action="ALLOW",
            source_zone_id="z1",
            destination_zone_id="z2",
            protocol="udp",
            port_ranges=("53",),
        )
        assert policy.protocol == "udp"
        assert policy.port_ranges == ("53",)


class TestFirewallGroup:
    def test_basic(self):
        group = FirewallGroup(
            id="g1",
            name="DNS Servers",
            group_type="address-group",
            members=("1.1.1.1", "8.8.8.8"),
        )
        assert len(group.members) == 2
        assert group.group_type == "address-group"
