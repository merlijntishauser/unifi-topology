"""Tests for SVG WAN label formatting helpers."""

from __future__ import annotations

from unifi_topology.model.topology import WanInfo, WanInterface
from unifi_topology.render.svg_labels import _build_wan_label_lines, _format_wan_speed


class TestFormatWanSpeed:
    def test_none_returns_none(self):
        assert _format_wan_speed(None) is None

    def test_zero_returns_none(self):
        assert _format_wan_speed(0) is None

    def test_megabit_format(self):
        assert _format_wan_speed(100) == "100MbE"

    def test_gigabit_format(self):
        assert _format_wan_speed(1000) == "1GbE"

    def test_ten_gigabit_format(self):
        assert _format_wan_speed(10000) == "10GbE"

    def test_fractional_gigabit(self):
        assert _format_wan_speed(2500) == "2.5GbE"


class TestBuildWanLabelLines:
    def test_single_wan_basic(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        info = WanInfo(wan1=wan, wan2=None)
        lines = _build_wan_label_lines(info)
        assert len(lines) >= 1
        assert "WAN1" in lines[0] or any("1GbE" in line for line in lines)

    def test_single_wan_with_label(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="1.2.3.4",
            enabled=True,
            label="KPN Fiber",
        )
        info = WanInfo(wan1=wan, wan2=None)
        lines = _build_wan_label_lines(info)
        assert any("KPN Fiber" in line for line in lines)

    def test_single_wan_with_isp_speed(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="1.2.3.4",
            enabled=True,
            isp_speed="500/500",
        )
        info = WanInfo(wan1=wan, wan2=None)
        lines = _build_wan_label_lines(info)
        assert any("ISP 500/500" in line for line in lines)

    def test_dual_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(port_idx=9, link_speed=100, ip_address=None, enabled=True)
        info = WanInfo(wan1=wan1, wan2=wan2)
        lines = _build_wan_label_lines(info)
        assert any("WAN1" in line for line in lines)
        assert any("WAN2" in line for line in lines)

    def test_dual_wan_with_disabled_wan2(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(
            port_idx=9, link_speed=None, ip_address=None, enabled=False, label="Backup"
        )
        info = WanInfo(wan1=wan1, wan2=wan2)
        lines = _build_wan_label_lines(info)
        assert any("disabled" in line for line in lines)

    def test_ip_address_included(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="203.0.113.1", enabled=True)
        info = WanInfo(wan1=wan, wan2=None)
        lines = _build_wan_label_lines(info)
        assert any("203.0.113.1" in line for line in lines)
