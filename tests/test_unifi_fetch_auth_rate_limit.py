import pytest

from tests.unifi_fetch_helpers import config
from unifi_topology.adapters import unifi
from unifi_topology.adapters.unifi_api import UnifiAuthError

pytestmark = pytest.mark.integration


def test_rate_limited_auth_error_skips_legacy_retry(monkeypatch, tmp_path):
    import json
    import time

    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    calls = {"init_count": 0}

    def fake_create_client(config, *, is_udm_pro):
        calls["init_count"] += 1
        raise UnifiAuthError("Too Many Requests", status_code=429)

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    cache_path = tmp_path / f"devices_{unifi._cache_key(config().url, config().site, 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )
    devices = list(unifi.fetch_devices(config()))
    assert calls["init_count"] == 1
    from tests.unifi_fetch_helpers import first_mapping

    assert first_mapping(devices)["stale"] is True


def test_rate_limited_auth_error_raises_without_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")

    def fake_create_client(config, *, is_udm_pro):
        raise UnifiAuthError("Too Many Requests", status_code=429)

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    with pytest.raises(UnifiAuthError) as excinfo:
        unifi.fetch_devices(config())
    assert excinfo.value.status_code == 429
