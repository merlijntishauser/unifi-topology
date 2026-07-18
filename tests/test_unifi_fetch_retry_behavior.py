import pytest

from tests.unifi_fetch_helpers import config, first_mapping
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


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
    devices = list(unifi.fetch_devices(config()))
    assert calls["count"] == 2
    assert first_mapping(devices)["ok"] is True


def test_call_with_retries_propagates_final_error(monkeypatch):
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")

    def failing_call():
        raise TimeoutError("request timed out")

    with pytest.raises(TimeoutError):
        unifi._call_with_retries("slow", failing_call)


def test_auth_errors_are_not_retried(monkeypatch):
    from unifi_topology.adapters.unifi_api import UnifiAuthError

    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")
    calls = {"count": 0}

    def failing():
        calls["count"] += 1
        raise UnifiAuthError("bad credentials")

    with pytest.raises(UnifiAuthError):
        unifi._call_with_retries("auth", failing)
    assert calls["count"] == 1


def test_transient_errors_are_retried(monkeypatch):
    import requests

    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")
    calls = {"count": 0}

    def failing():
        calls["count"] += 1
        raise requests.ConnectionError("network down")

    with pytest.raises(requests.ConnectionError):
        unifi._call_with_retries("fetch", failing)
    assert calls["count"] == 3
