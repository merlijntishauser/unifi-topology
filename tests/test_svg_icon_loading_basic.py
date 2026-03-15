from pathlib import Path

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_icons as svg_icons_module


def test_load_icons_missing_files_returns_empty(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    assert svg_module._load_icons() == {}


def test_load_isometric_icons_missing_files_returns_empty(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    assert svg_icons_module._load_isometric_icons() == {}


def test_load_isometric_icons_isometric():
    icons = svg_icons_module._load_isometric_icons("isometric")
    assert "gateway" in icons
    assert "switch" in icons
    assert "ap" in icons
    assert "client" in icons
    assert "other" in icons
    assert all(value.startswith("data:image/svg+xml;base64,") for value in icons.values())


def test_load_isometric_icons_modern():
    icons = svg_icons_module._load_isometric_icons("modern")
    assert "gateway" in icons
    assert "switch" in icons
    assert "ap" in icons
    assert "client" in icons
    assert "other" in icons
    assert all(value.startswith("data:image/svg+xml;base64,") for value in icons.values())


def test_load_isometric_icons_fallback_to_isometric():
    icons = svg_icons_module._load_isometric_icons("nonexistent_set")
    assert "gateway" in icons
    assert icons


def test_load_icons_isometric():
    icons = svg_module._load_icons("isometric")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_icons_modern():
    icons = svg_module._load_icons("modern")
    assert "gateway" in icons
    assert "switch" in icons
