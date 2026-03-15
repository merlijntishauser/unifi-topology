"""Tests for edge port matching helpers."""

from __future__ import annotations

from tests.edge_port_helpers import make_port
from unifi_topology.model.edges import _lldp_candidates, _match_port_by_name, _match_port_by_number
from unifi_topology.model.lldp import LLDPEntry


def test_lldp_candidates_both_fields():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name="eth0")
    assert _lldp_candidates(entry) == ["eth0", "Port 1"]


def test_lldp_candidates_only_local_port_name():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name="eth0")
    assert _lldp_candidates(entry) == ["eth0"]


def test_lldp_candidates_only_port_id():
    entry = LLDPEntry(chassis_id="aa", port_id="Port 1", local_port_name=None)
    assert _lldp_candidates(entry) == ["Port 1"]


def test_lldp_candidates_neither_field():
    entry = LLDPEntry(chassis_id="aa", port_id="", local_port_name=None)
    assert _lldp_candidates(entry) == []


def test_match_port_by_name_matches_ifname():
    ports = [make_port(1, ifname="eth0"), make_port(2, ifname="eth1")]
    assert _match_port_by_name(["eth1"], ports) == 2


def test_match_port_by_name_matches_name():
    ports = [make_port(3, name="Port 3")]
    assert _match_port_by_name(["Port 3"], ports) == 3


def test_match_port_by_name_case_insensitive():
    ports = [make_port(1, ifname="ETH0")]
    assert _match_port_by_name(["eth0"], ports) == 1


def test_match_port_by_name_no_match():
    ports = [make_port(1, ifname="eth0")]
    assert _match_port_by_name(["eth5"], ports) is None


def test_match_port_by_name_empty_candidates():
    ports = [make_port(1, ifname="eth0")]
    assert _match_port_by_name([], ports) is None


def test_match_port_by_number_matches():
    ports = [make_port(5), make_port(9)]
    assert _match_port_by_number(["Port 9"], ports) == 9


def test_match_port_by_number_no_port_match():
    ports = [make_port(1), make_port(2)]
    assert _match_port_by_number(["Port 9"], ports) is None


def test_match_port_by_number_no_extractable_number():
    ports = [make_port(1)]
    assert _match_port_by_number(["wan"], ports) is None
