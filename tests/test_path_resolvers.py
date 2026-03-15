"""Tests for public path resolver entry points."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from unifi_topology.paths import (
    resolve_cache_dir,
    resolve_env_file,
    resolve_input_file,
    resolve_theme_path,
)


def test_resolve_input_file_returns_resolved_path(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text("{}")
    result = resolve_input_file(str(path), extensions={".json"}, label="Test")
    assert result == path.resolve()


def test_resolve_input_file_rejects_nonexistent(tmp_path: Path):
    path = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="does not exist"):
        resolve_input_file(str(path), extensions={".json"}, label="Test")


def test_resolve_input_file_rejects_directory(tmp_path: Path):
    path = tmp_path / "dir.json"
    path.mkdir()
    with pytest.raises(ValueError, match="must be a file"):
        resolve_input_file(str(path), extensions={".json"}, label="Test")


def test_resolve_input_file_allows_nonexistent_when_flagged(tmp_path: Path):
    path = tmp_path / "missing.json"
    result = resolve_input_file(str(path), extensions={".json"}, label="Test", require_exists=False)
    assert result == path.resolve()


def test_resolve_input_file_rejects_wrong_extension(tmp_path: Path):
    path = tmp_path / "data.txt"
    path.write_text("content")
    with pytest.raises(ValueError, match="must have one of"):
        resolve_input_file(str(path), extensions={".json"}, label="Test")


def test_resolve_theme_path_accepts_yml(tmp_path: Path):
    path = tmp_path / "theme.yml"
    path.write_text("key: value")
    result = resolve_theme_path(str(path))
    assert result == path.resolve()


def test_resolve_theme_path_accepts_yaml(tmp_path: Path):
    path = tmp_path / "theme.yaml"
    path.write_text("key: value")
    result = resolve_theme_path(str(path))
    assert result == path.resolve()


def test_resolve_theme_path_rejects_json(tmp_path: Path):
    path = tmp_path / "theme.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="must have one of"):
        resolve_theme_path(str(path))


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


def test_resolve_input_file_rejects_path_traversal(tmp_path: Path):
    evil = tmp_path / "sub" / ".." / ".." / ".." / "etc" / "passwd.json"
    with pytest.raises(ValueError):
        resolve_input_file(str(evil), extensions={".json"}, label="Test")


def test_allowed_paths_env_extends_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    path = extra_dir / "data.json"
    path.write_text("{}")
    monkeypatch.setenv("UNIFI_ALLOWED_PATHS", str(extra_dir))
    result = resolve_input_file(str(path), extensions={".json"}, label="Test")
    assert result == path.resolve()
