"""Tests for path extension guard helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from unifi_topology.paths import _ensure_extension, _normalize_extensions


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
