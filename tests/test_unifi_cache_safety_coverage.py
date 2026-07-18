"""Cache safety coverage for unifi.py."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import patch

from unifi_topology.adapters import unifi


def test_cache_lock_release_oserror_is_swallowed(tmp_path):
    lock_target = tmp_path / "test.json"
    lock_target.write_text("{}", encoding="utf-8")
    with patch.object(unifi, "_release_cache_lock", side_effect=OSError("boom")):
        with unifi._cache_lock(lock_target):
            pass


def test_is_cache_dir_safe_returns_true_for_nonexistent(tmp_path):
    assert unifi._is_cache_dir_safe(tmp_path / "does_not_exist") is True


def test_is_cache_dir_safe_stat_failure(tmp_path):
    target = tmp_path / "dir"
    target.mkdir()
    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "stat", side_effect=OSError("permission denied")),
    ):
        assert unifi._is_cache_dir_safe(target) is False


def test_is_cache_dir_safe_world_writable(tmp_path):
    target = tmp_path / "unsafe"
    target.mkdir()
    target.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    assert unifi._is_cache_dir_safe(target) is False
    target.chmod(stat.S_IRWXU)


def test_load_cache_with_age_corrupt_file(tmp_path):
    cache_path = tmp_path / "corrupt.json"
    cache_path.write_text("not valid json {{{", encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


def test_cache_dir_without_pytest_env(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("UNIFI_CACHE_DIR", raising=False)
    assert ".cache/unifi_network_maps" in str(unifi._cache_dir())


def test_cache_dir_never_raises_when_resolution_fails(monkeypatch):
    from unifi_topology.adapters import _cache_store

    def always_fail(_value):
        raise ValueError("Cache directory parent must not be a symlink: /var")

    monkeypatch.setattr(_cache_store, "resolve_cache_dir", always_fail)
    result = _cache_store._cache_dir()
    assert isinstance(result, Path)
