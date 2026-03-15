"""Tests for input and theme path resolvers."""

from __future__ import annotations

from pathlib import Path

import pytest

from unifi_topology.paths import resolve_input_file, resolve_theme_path


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


def test_resolve_input_file_rejects_path_traversal(tmp_path: Path):
    evil = tmp_path / "sub" / ".." / ".." / ".." / "etc" / "passwd.json"
    with pytest.raises(ValueError):
        resolve_input_file(str(evil), extensions={".json"}, label="Test")
