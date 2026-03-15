"""Tests for low-level path validation helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from unifi_topology.paths import (
    _ensure_extension,
    _ensure_no_symlink,
    _ensure_no_symlink_in_parents,
    _ensure_within_allowed,
    _normalize_extensions,
)


def test_normalize_extensions_adds_dot():
    assert _normalize_extensions(["json", "yaml"]) == {".json", ".yaml"}


def test_normalize_extensions_preserves_dot():
    assert _normalize_extensions([".json"]) == {".json"}


def test_normalize_extensions_lowercases():
    assert _normalize_extensions([".JSON", "YAML"]) == {".json", ".yaml"}


def test_normalize_extensions_strips_whitespace():
    assert _normalize_extensions(["  .json  "]) == {".json"}


def test_normalize_extensions_skips_empty():
    assert _normalize_extensions(["", "  ", ".json"]) == {".json"}


def test_ensure_extension_accepts_valid(tmp_path: Path):
    path = tmp_path / "file.json"
    _ensure_extension(path, [".json"], label="Test")


def test_ensure_extension_rejects_wrong_extension(tmp_path: Path):
    path = tmp_path / "file.txt"
    with pytest.raises(ValueError, match="must have one of"):
        _ensure_extension(path, [".json"], label="Test")


def test_ensure_extension_rejects_missing_extension(tmp_path: Path):
    path = tmp_path / "file"
    with pytest.raises(ValueError, match="must have one of"):
        _ensure_extension(path, [".json"], label="Test")


def test_ensure_extension_allows_missing_when_flagged(tmp_path: Path):
    path = tmp_path / "file"
    _ensure_extension(path, [".json"], label="Test", allow_missing=True)


def test_ensure_extension_skips_when_no_extensions(tmp_path: Path):
    path = tmp_path / "anything"
    _ensure_extension(path, None, label="Test")


def test_ensure_within_allowed_accepts_child(tmp_path: Path):
    child = tmp_path / "sub" / "file.txt"
    _ensure_within_allowed(child, [tmp_path], label="Test")


def test_ensure_within_allowed_rejects_outside(tmp_path: Path):
    outside = Path("/etc/passwd")
    with pytest.raises(ValueError, match="must be within"):
        _ensure_within_allowed(outside, [tmp_path], label="Test")


def test_ensure_within_allowed_accepts_multiple_roots(tmp_path: Path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    child = root_b / "file.txt"
    _ensure_within_allowed(child, [root_a, root_b], label="Test")


@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks need special privileges on Windows")
def test_ensure_no_symlink_rejects_symlink(tmp_path: Path):
    target = tmp_path / "target"
    target.touch()
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="must not be a symlink"):
        _ensure_no_symlink(link, label="Test")


def test_ensure_no_symlink_accepts_regular_file(tmp_path: Path):
    regular = tmp_path / "file.txt"
    regular.touch()
    _ensure_no_symlink(regular, label="Test")


def test_ensure_no_symlink_accepts_nonexistent(tmp_path: Path):
    missing = tmp_path / "missing"
    _ensure_no_symlink(missing, label="Test")


@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks need special privileges on Windows")
def test_ensure_no_symlink_in_parents_rejects_symlinked_parent(tmp_path: Path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)
    child = link_dir / "file.txt"
    with pytest.raises(ValueError, match="parent must not be a symlink"):
        _ensure_no_symlink_in_parents(child, label="Test")


def test_ensure_no_symlink_in_parents_accepts_normal_parents(tmp_path: Path):
    child = tmp_path / "a" / "b" / "file.txt"
    _ensure_no_symlink_in_parents(child, label="Test")
