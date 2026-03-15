"""Tests for device stats normalization model mapping."""

import pytest

from unifi_topology.model.device_stats_coerce import normalize_device_stats

pytestmark = pytest.mark.unit


class TestNormalizeDeviceStatsModels:
    def test_type_normalization_ugw(self):
        raw = [{"mac": "aa", "type": "ugw"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "gateway"

    def test_type_normalization_udm(self):
        raw = [{"mac": "aa", "type": "udm"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "gateway"

    def test_type_normalization_usw(self):
        raw = [{"mac": "aa", "type": "usw"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "switch"

    def test_type_normalization_uap(self):
        raw = [{"mac": "aa", "type": "uap"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "ap"

    def test_type_unknown_preserved(self):
        raw = [{"mac": "aa", "type": "uxg"}]
        result = normalize_device_stats(raw)
        assert result[0].type == "uxg"

    def test_multiple_devices(self):
        raw = [
            {"mac": "aa", "type": "usw", "name": "Switch"},
            {"mac": "bb", "type": "uap", "name": "AP"},
        ]
        result = normalize_device_stats(raw)
        assert len(result) == 2
        assert result[0].name == "Switch"
        assert result[0].type == "switch"
        assert result[1].name == "AP"
        assert result[1].type == "ap"
