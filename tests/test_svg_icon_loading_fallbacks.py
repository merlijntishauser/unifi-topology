import unifi_topology.render.svg_icons as svg_icons_module


def test_load_icons_primary_missing_falls_back_to_isometric(monkeypatch):
    patched_sets = {
        "custom": (
            "nonexistent-dir",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_icons("custom")
    assert "gateway" in icons
    assert icons["gateway"].startswith("data:image/svg+xml;base64,")


def test_load_icons_no_filename_in_primary_falls_back(monkeypatch):
    patched_sets = {
        "sparse": (
            "",
            "isometric",
            {},
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_icons("sparse")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_icons_no_fallback_filename_skips(monkeypatch):
    patched_sets = {
        "isometric": (
            "",
            "isometric",
            {},
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
    }
    patched_sets["isometric"] = ("", "isometric", {}, svg_icons_module._ISO_ICON_FILES_ISOMETRIC)
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    assert len(svg_icons_module._load_icons("isometric")) == 0


def test_load_isometric_icons_primary_missing_falls_back(monkeypatch):
    patched_sets = {
        "custom": (
            "",
            "nonexistent-iso-dir",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_isometric_icons("custom")
    assert "gateway" in icons
    assert icons["gateway"].startswith("data:image/svg+xml;base64,")


def test_load_isometric_icons_no_filename_in_primary_falls_back(monkeypatch):
    patched_sets = {
        "sparse": (
            "",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            {},
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_isometric_icons("sparse")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_isometric_icons_no_fallback_filename_skips(monkeypatch):
    patched_sets = {
        "isometric": (
            "",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            {},
        ),
    }
    patched_sets["isometric"] = (
        "",
        "isometric",
        svg_icons_module._ICON_FILES_ISOMETRIC,
        {},
    )
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    assert len(svg_icons_module._load_isometric_icons("isometric")) == 0
