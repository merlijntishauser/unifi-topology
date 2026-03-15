"""Tests for environment and cache path resolvers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from unifi_topology.paths import resolve_cache_dir, resolve_env_file, resolve_input_file


def test_resolve_env_file_accepts_dotenv(tmp_path: Path):
    path = tmp_path / ".env"
    path.write_text("KEY=val")
    result = resolve_env_file(str(path))
    assert result == path.resolve()


def test_resolve_env_file_accepts_name_ending_with_env(tmp_path: Path):
    path = tmp_path / "production.env"
    path.write_text("KEY=val")
    result = resolve_env_file(str(path))
    assert result == path.resolve()


def test_resolve_env_file_rejects_non_env(tmp_path: Path):
    path = tmp_path / "config.txt"
    path.write_text("KEY=val")
    with pytest.raises(ValueError, match="must end with .env"):
        resolve_env_file(str(path))


def test_resolve_env_file_accepts_nonexistent_dotenv(tmp_path: Path):
    path = tmp_path / ".env"
    result = resolve_env_file(str(path))
    assert result == path.resolve()


def test_resolve_cache_dir_accepts_normal_dir(tmp_path: Path):
    path = tmp_path / "cache"
    path.mkdir()
    result = resolve_cache_dir(str(path))
    assert result == path.resolve()


@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks need special privileges on Windows")
def test_resolve_cache_dir_rejects_symlink(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="must not be a symlink"):
        resolve_cache_dir(str(link))


def test_allowed_paths_env_extends_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    path = extra_dir / "data.json"
    path.write_text("{}")
    monkeypatch.setenv("UNIFI_ALLOWED_PATHS", str(extra_dir))
    result = resolve_input_file(str(path), extensions={".json"}, label="Test")
    assert result == path.resolve()
