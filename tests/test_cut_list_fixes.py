"""Regression tests for the smaller findings of the November 2026 code review."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from unifi_topology import paths
from unifi_topology.adapters import _cache_store, unifi
from unifi_topology.adapters.config import Config
from unifi_topology.model.classify import classify_client_type
from unifi_topology.model.edges import enrich_edges_with_active_vlans
from unifi_topology.model.firewall_coerce import normalize_firewall_policies
from unifi_topology.model.topology import Edge
from unifi_topology.model.vlans import build_network_vlan_map, build_vlan_names
from unifi_topology.paths import _ensure_no_symlink_in_parents
from unifi_topology.render.mermaid import render_mermaid
from unifi_topology.render.theme import _coerce_icon_set

_POSIX_ONLY = pytest.mark.skipif(sys.platform == "win32", reason="POSIX ownership semantics")


def test_active_vlans_reach_uplink_trunks_from_downstream_clients():
    edges = [
        Edge("gw", "core", vlans=(1, 10, 20)),
        Edge("core", "sw", vlans=(1, 10, 20)),
        Edge("core", "ap", vlans=(1, 20)),
    ]
    client_edges = [Edge("sw", "pc", active_vlans=(10,)), Edge("ap", "phone", active_vlans=(20,))]
    enriched = enrich_edges_with_active_vlans(edges, client_edges)
    assert [edge.active_vlans for edge in enriched] == [(10, 20), (10,), (20,)]


def test_wan_and_vpn_networks_do_not_claim_vlan_1():
    networks = [
        {"_id": "lan", "name": "Default", "purpose": "corporate"},
        {"_id": "wan", "name": "Internet 1", "purpose": "wan"},
        {"_id": "vpn", "name": "Teleport", "purpose": "remote-user-vpn"},
    ]
    assert build_vlan_names(reversed(networks)) == {1: "Default"}
    assert build_network_vlan_map(networks) == {"lan": 1}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Cameron's iPhone", "phone"),
        ("Engineering-Laptop", "client"),
        ("Jonas MacBook", "client"),
        ("FrontDoorCam", "camera"),
        ("garage-cam2", "camera"),
        ("LivingRoomTV", "tv"),
        ("HP LaserJet", "printer"),
    ],
)
def test_client_names_match_whole_words_only(name: str, expected: str):
    assert classify_client_type({"name": name}) == expected


@pytest.mark.parametrize("vendor", ["Apple, Inc.", "Ubiquiti Inc"])
def test_broad_vendors_do_not_decide_the_category(vendor: str):
    assert classify_client_type({"name": "device-1234", "oui": vendor}) == "client"


def test_client_session_key_tracks_password_and_tls_setting():
    def key(password: str = "one", verify_ssl: bool = True) -> tuple[object, ...]:
        config = Config(
            url="https://c", site="default", user="u", password=password, verify_ssl=verify_ssl
        )
        return unifi._client_cache_key(config, is_udm_pro=True)

    assert key() == key()
    assert key() != key(password="two")
    assert key() != key(verify_ssl=False)
    assert "one" not in key()


def test_theme_accepts_every_bundled_icon_set():
    assert _coerce_icon_set("unifi", "isometric") == "unifi"
    assert _coerce_icon_set("nonexistent", "isometric") == "isometric"


def test_mermaid_applies_standard_link_style_to_the_diagram():
    output = render_mermaid([Edge("a", "b"), Edge("b", "c", wireless=True)])
    standard = "stroke:#2ecc71,stroke-width:2px,arrowhead:none"
    assert f"  linkStyle default {standard};" in output
    assert f"  linkStyle 1 {standard},stroke-dasharray: 5 4;" in output


def test_firewall_schedule_object_and_boolean_ipsec_are_not_stringified():
    (policy,) = normalize_firewall_policies(
        [{"_id": "p1", "name": "Allow", "schedule": {"mode": "ALWAYS"}, "match_ip_sec": False}]
    )
    assert policy.schedule == "ALWAYS"
    assert policy.match_ip_sec == ""


@_POSIX_ONLY
def test_root_owned_symlinked_parent_is_accepted(tmp_path: Path, monkeypatch):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    if os.geteuid() != 0:
        assert not paths._is_system_symlink(link)
        with pytest.raises(ValueError, match="must not be a symlink"):
            _ensure_no_symlink_in_parents(link / "cache", label="Cache directory")

    monkeypatch.setattr(paths, "_is_system_symlink", lambda _path: True)
    _ensure_no_symlink_in_parents(link / "cache", label="Cache directory")


@_POSIX_ONLY
def test_symlinked_cache_dir_is_never_used(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    link = tmp_path / "link"
    os.symlink(real, link)
    assert _cache_store._is_cache_dir_safe(real)
    assert not _cache_store._is_cache_dir_safe(link)
