import json
import os
import time

import pytest

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config
from unifi_topology.adapters.unifi_api import UnifiAuthError

pytestmark = pytest.mark.integration


def _config() -> Config:
    return Config(
        url="https://example",
        site="default",
        user="user",
        password="pass",
        verify_ssl=True,
    )


def _first_mapping(values: list[object]) -> dict[str, object]:
    value = values[0]
    assert isinstance(value, dict)
    return value


def test_fetch_devices_falls_back_on_auth_error(monkeypatch):
    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("bad auth")

        class Client:
            def get_devices(self, site, *, detailed=False):
                return [object(), object()]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    devices = list(unifi.fetch_devices(_config()))
    assert len(devices) == 2


def test_create_client_passes_config(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = Config(
        url="https://example", site="default", user="user", password="pass", verify_ssl=False
    )
    unifi._create_client(config, is_udm_pro=True)
    assert captured["verify_ssl"] is False


def test_fetch_clients_falls_back_on_auth_error(monkeypatch):
    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("bad auth")

        class Client:
            def get_clients(self, site):
                return [object()]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    clients = list(unifi.fetch_clients(_config()))
    assert len(clients) == 1


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
    config = _config()
    cache_path = tmp_path / f"devices_{unifi._cache_key(config.url, config.site, 'True')}.json"
    unifi._save_cache(cache_path, [{"name": "cached"}])

    def fail_init(*_args, **_kwargs):
        raise AssertionError("should not fetch when cache is valid")

    monkeypatch.setattr(unifi, "_create_client", fail_init)
    devices = list(unifi.fetch_devices(config))
    assert _first_mapping(devices)["name"] == "cached"


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
    config = Config(url="url", site="default", user="user", password="pass", verify_ssl=True)
    devices = list(unifi.fetch_devices(config, use_cache=False))
    assert calls["count"] == 1
    assert _first_mapping(devices)["name"] == "fresh"


def test_fetch_clients_cache_expired(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    config = _config()
    cache_path = tmp_path / f"clients_{unifi._cache_key(config.url, config.site)}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_clients(self, site):
            return [{"fresh": True}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    clients = list(unifi.fetch_clients(config))
    assert _first_mapping(clients)["fresh"] is True


def test_fetch_devices_uses_stale_cache_on_error(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    config = _config()
    cache_path = tmp_path / f"devices_{unifi._cache_key(config.url, config.site, 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_devices(self, site, *, detailed=False):
            raise RuntimeError("boom")

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    devices = list(unifi.fetch_devices(config))
    assert _first_mapping(devices)["stale"] is True


def test_fetch_clients_uses_stale_cache_on_error(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    config = _config()
    cache_path = tmp_path / f"clients_{unifi._cache_key(config.url, config.site)}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )

    class Client:
        def get_clients(self, site):
            raise RuntimeError("boom")

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    clients = list(unifi.fetch_clients(config))
    assert _first_mapping(clients)["stale"] is True


def test_fetch_devices_retries(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("boom")
            return [{"ok": True}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    devices = list(unifi.fetch_devices(_config()))
    assert calls["count"] == 2
    assert _first_mapping(devices)["ok"] is True


def test_call_with_retries_times_out(monkeypatch):
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")
    monkeypatch.setenv("UNIFI_REQUEST_TIMEOUT_SECONDS", "0.01")

    def slow_call():
        time.sleep(0.05)
        return "ok"

    with pytest.raises(TimeoutError):
        unifi._call_with_retries("slow", slow_call)


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
    config = Config(url="url", site="default", user="user", password="pass", verify_ssl=True)
    devices = list(unifi.fetch_devices(config))
    assert called["count"] == 1
    assert _first_mapping(devices)["name"] == "fresh"


def test_rate_limited_auth_error_skips_legacy_retry(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    calls = {"init_count": 0}

    def fake_create_client(config, *, is_udm_pro):
        calls["init_count"] += 1
        raise UnifiAuthError("HTTP 429 Too Many Requests")

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    config = _config()
    cache_path = tmp_path / f"devices_{unifi._cache_key(config.url, config.site, 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )
    devices = list(unifi.fetch_devices(config))
    assert calls["init_count"] == 1
    assert _first_mapping(devices)["stale"] is True


def test_rate_limited_auth_error_raises_without_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")

    def fake_create_client(config, *, is_udm_pro):
        raise UnifiAuthError("HTTP 429 Too Many Requests")

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    with pytest.raises(UnifiAuthError, match="429"):
        unifi.fetch_devices(_config())


def test_non_429_auth_error_retries_legacy(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))

    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("Invalid credentials")

        class Client:
            def get_devices(self, site, *, detailed=False):
                return [{"ok": True}]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    devices = list(unifi.fetch_devices(_config()))
    assert len(devices) == 1


def test_fetch_device_stats_calls_get_devices_detailed(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, bool]] = []

    class Client:
        def get_devices(self, site, *, detailed=False):
            calls.append((site, detailed))
            return [{"mac": "aa", "type": "usw"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    result = list(unifi.fetch_device_stats(_config()))
    assert len(result) == 1
    assert calls == [("default", True)]


def test_fetch_device_stats_default_no_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    config = _config()
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config.url, config.site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])
    called = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            called["count"] += 1
            return [{"mac": "fresh"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    result = list(unifi.fetch_device_stats(config))
    assert called["count"] == 1
    assert _first_mapping(result)["mac"] == "fresh"


def test_fetch_device_stats_with_cache_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    config = _config()
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config.url, config.site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])

    def fail_init(*_args, **_kwargs):
        raise AssertionError("should not fetch when cache is valid")

    monkeypatch.setattr(unifi, "_create_client", fail_init)
    result = list(unifi.fetch_device_stats(config, use_cache=True))
    assert _first_mapping(result)["mac"] == "cached"
