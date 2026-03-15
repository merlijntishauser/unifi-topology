import json
import os
import time

import pytest

from tests.unifi_fetch_helpers import config, first_mapping
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


def test_fetch_devices_uses_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"devices_{unifi._cache_key(config().url, config().site, 'True')}.json"
    unifi._save_cache(cache_path, [{"name": "cached"}])

    def fail_init(*_args, **_kwargs):
        raise AssertionError("should not fetch when cache is valid")

    monkeypatch.setattr(unifi, "_create_client", fail_init)
    devices = list(unifi.fetch_devices(config()))
    assert first_mapping(devices)["name"] == "cached"


def test_fetch_devices_skips_cache_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"devices_{unifi._cache_key('url', 'default', 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time(), "data": [{"name": "cached"}]}),
        encoding="utf-8",
    )
    calls = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            calls["count"] += 1
            return [{"name": "fresh"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    client_config = Config(url="url", site="default", user="user", password="pass", verify_ssl=True)
    devices = list(unifi.fetch_devices(client_config, use_cache=False))
    assert calls["count"] == 1
    assert first_mapping(devices)["name"] == "fresh"


def test_fetch_clients_cache_expired(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"clients_{unifi._cache_key(config().url, config().site)}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_clients(self, site):
            return [{"fresh": True}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    clients = list(unifi.fetch_clients(config()))
    assert first_mapping(clients)["fresh"] is True


def test_fetch_devices_uses_stale_cache_on_error(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"devices_{unifi._cache_key(config().url, config().site, 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_devices(self, site, *, detailed=False):
            raise RuntimeError("boom")

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    devices = list(unifi.fetch_devices(config()))
    assert first_mapping(devices)["stale"] is True


def test_fetch_clients_uses_stale_cache_on_error(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"clients_{unifi._cache_key(config().url, config().site)}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_clients(self, site):
            raise RuntimeError("boom")

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    clients = list(unifi.fetch_clients(config()))
    assert first_mapping(clients)["stale"] is True


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


def test_fetch_device_stats_default_no_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config().url, config().site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])
    called = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            called["count"] += 1
            return [{"mac": "fresh"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    result = list(unifi.fetch_device_stats(config()))
    assert called["count"] == 1
    assert first_mapping(result)["mac"] == "fresh"


def test_fetch_device_stats_with_cache_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config().url, config().site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])

    def fail_init(*_args, **_kwargs):
        raise AssertionError("should not fetch when cache is valid")

    monkeypatch.setattr(unifi, "_create_client", fail_init)
    result = list(unifi.fetch_device_stats(config(), use_cache=True))
    assert first_mapping(result)["mac"] == "cached"
