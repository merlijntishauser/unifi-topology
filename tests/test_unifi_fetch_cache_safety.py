import json
import os
import time

import pytest

from tests.unifi_fetch_helpers import first_mapping
from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

pytestmark = pytest.mark.integration


def test_cache_dir_rejects_symlink(monkeypatch, tmp_path):
    if not hasattr(os, "symlink"):
        pytest.skip("OS does not support symlinks")
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    os.symlink(real_dir, link_dir)
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(link_dir))
    cache_dir = unifi._cache_dir()
    assert cache_dir != link_dir
    assert not cache_dir.is_symlink()


def test_fetch_devices_skips_cache_when_dir_is_world_writable(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"devices_{unifi._cache_key('url', 'default', 'True')}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"timestamp": time.time(), "data": [{"name": "cached"}]}),
        encoding="utf-8",
    )
    tmp_path.chmod(0o777)
    called = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            called["count"] += 1
            return [{"name": "fresh"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    client_config = Config(url="url", site="default", user="user", password="pass", verify_ssl=True)
    devices = list(unifi.fetch_devices(client_config))
    assert called["count"] == 1
    assert first_mapping(devices)["name"] == "fresh"
