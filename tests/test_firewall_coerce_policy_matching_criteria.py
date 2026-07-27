"""Tests for domain, application, and client-MAC matching criteria (#68).

A rule narrowed to a handful of domains was indistinguishable from a wide-open
one, so consumers doing static analysis graded it as unrestricted. The payload
shapes below are taken from a live 156-policy zone-based ruleset.
"""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


def _policy(**overrides):
    entry = {
        "_id": "p1",
        "name": "x",
        "enabled": True,
        "action": "ALLOW",
        "source": {"zone_id": "z1"},
        "destination": {"zone_id": "z2"},
    }
    entry.update(overrides)
    return normalize_firewall_policies([entry])[0]


class TestWebDomainMatching:
    def test_web_domains_are_exposed(self):
        policy = _policy(
            protocol="all",
            destination={
                "zone_id": "z2",
                "matching_target": "WEB",
                "matching_target_type": "SPECIFIC",
                "port_matching_type": "ANY",
                "web_domains": ["cloud.tesla.com", "eic-hcss.lgthinq.com"],
                "web_matching_type": "CUSTOM",
            },
        )
        assert policy.destination_web_domains == ("cloud.tesla.com", "eic-hcss.lgthinq.com")
        assert policy.destination_web_matching_type == "CUSTOM"

    def test_a_domain_restricted_rule_is_distinguishable_from_an_open_one(self):
        """The regression from #68: both have protocol=all and no ports."""
        restricted = _policy(
            protocol="all",
            destination={
                "zone_id": "z2",
                "matching_target": "WEB",
                "port_matching_type": "ANY",
                "web_domains": ["cloud.tesla.com"],
            },
        )
        wide_open = _policy(
            protocol="all",
            destination={"zone_id": "z2", "matching_target": "ANY", "port_matching_type": "ANY"},
        )
        assert restricted.protocol == wide_open.protocol
        assert restricted.port_ranges == wide_open.port_ranges == ()
        assert restricted.destination_matching_target == "WEB"
        assert wide_open.destination_matching_target == "ANY"


class TestApplicationMatching:
    def test_app_ids_are_exposed_as_strings(self):
        """The controller sends integers; every other id on the model is a str."""
        policy = _policy(
            destination={"zone_id": "z2", "matching_target": "APP", "app_ids": [524444]}
        )
        assert policy.destination_app_ids == ("524444",)
        assert policy.destination_matching_target == "APP"


class TestMatchingTarget:
    @pytest.mark.parametrize("target", ["ANY", "IP", "CLIENT", "APP", "WEB"])
    def test_target_is_reported_for_both_sides(self, target: str):
        policy = _policy(
            source={"zone_id": "z1", "matching_target": target},
            destination={"zone_id": "z2", "matching_target": target},
        )
        assert policy.source_matching_target == target
        assert policy.destination_matching_target == target

    def test_target_is_upper_cased(self):
        policy = _policy(destination={"zone_id": "z2", "matching_target": "web"})
        assert policy.destination_matching_target == "WEB"

    def test_missing_target_is_empty_not_any(self):
        """Absent is not the same as explicitly unrestricted."""
        assert _policy().destination_matching_target == ""

    def test_unknown_future_target_still_signals_restriction(self):
        """A criterion this model cannot parse must not read as unrestricted."""
        policy = _policy(destination={"zone_id": "z2", "matching_target": "REGION"})
        assert policy.destination_matching_target == "REGION"
        assert policy.destination_web_domains == ()
        assert policy.destination_app_ids == ()


class TestClientMacMatching:
    def test_client_macs_populate_source_mac_addresses(self):
        """Zone-based controllers send client_macs, not mac_addresses."""
        policy = _policy(
            source={
                "zone_id": "z1",
                "matching_target": "CLIENT",
                "client_macs": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
            }
        )
        assert policy.source_mac_addresses == ("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66")

    def test_legacy_mac_addresses_key_still_works(self):
        policy = _policy(source={"zone_id": "z1", "mac_addresses": ["aa:bb:cc:dd:ee:ff"]})
        assert policy.source_mac_addresses == ("aa:bb:cc:dd:ee:ff",)

    def test_client_macs_take_precedence_when_both_present(self):
        policy = _policy(
            source={
                "zone_id": "z1",
                "client_macs": ["aa:aa:aa:aa:aa:aa"],
                "mac_addresses": ["bb:bb:bb:bb:bb:bb"],
            }
        )
        assert policy.source_mac_addresses == ("aa:aa:aa:aa:aa:aa",)


class TestBackwardsCompatibility:
    def test_policies_without_criteria_default_to_empty(self):
        policy = _policy()
        assert policy.destination_web_domains == ()
        assert policy.destination_app_ids == ()
        assert policy.destination_web_matching_type == ""
        assert policy.source_matching_target == ""

    def test_non_dict_endpoint_blocks_are_tolerated(self):
        policy = _policy(source="not-a-dict", destination=None)
        assert policy.destination_web_domains == ()
        assert policy.destination_matching_target == ""
