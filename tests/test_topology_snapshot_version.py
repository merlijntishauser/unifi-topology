"""Snapshot version validation on load."""

import pytest

from unifi_topology.model.topology import Topology


def test_from_dict_accepts_current_version():
    data = Topology(timestamp="t").to_dict()
    restored = Topology.from_dict(data)
    assert restored.timestamp == "t"


def test_from_dict_accepts_missing_version():
    restored = Topology.from_dict({"devices": [], "clients": [], "edges": []})
    assert restored.devices == []


def test_from_dict_rejects_future_version():
    data = Topology(timestamp="t").to_dict()
    data["version"] = 999
    with pytest.raises(ValueError, match="version"):
        Topology.from_dict(data)
