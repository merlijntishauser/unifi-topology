"""Tests for inventory firmware helpers."""

from unifi_topology.model.inventory import _extract_fw_version


def test_extract_fw_version_camera():
    assert _extract_fw_version("UVC.SAV539g.v5.2.52.67.39be8f1.260203.0900") == "5.2.52.67"


def test_extract_fw_version_chime():
    assert _extract_fw_version("UP.esp32.v1.7.20.0.402a5ff.240910.0649") == "1.7.20.0"


def test_extract_fw_version_superlink():
    assert _extract_fw_version("LS.sav530q.v1.7.0.0.0631741.250926.1311") == "1.7.0.0"


def test_extract_fw_version_plain():
    assert _extract_fw_version("1.2.3") == "1.2.3"


def test_extract_fw_version_no_match():
    assert _extract_fw_version("unknown") == "unknown"
