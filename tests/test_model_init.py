"""Tests for model __init__.py lazy imports."""

import pytest

import unifi_topology.model as model_pkg


def test_lazy_import_mock_options():
    cls = getattr(model_pkg, "MockOptions")
    assert cls is not None


def test_lazy_import_generate_mock_payload():
    fn = getattr(model_pkg, "generate_mock_payload")
    assert callable(fn)


def test_lazy_import_unknown_attribute():
    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(model_pkg, "NoSuchThing")
