"""Tests for firewall group normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_groups

pytestmark = pytest.mark.unit


class TestNormalizeGroups:
    def test_basic(self):
        raw = [
            {
                "_id": "g1",
                "name": "DNS",
                "group_type": "address-group",
                "group_members": ["1.1.1.1", "8.8.8.8"],
            },
        ]
        groups = normalize_firewall_groups(raw)
        assert len(groups) == 1
        assert groups[0].members == ("1.1.1.1", "8.8.8.8")

    def test_empty_members(self):
        groups = normalize_firewall_groups(
            [{"_id": "g1", "name": "Empty", "group_type": "port-group"}]
        )
        assert groups[0].members == ()
