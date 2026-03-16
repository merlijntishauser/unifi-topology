"""Tests for Jinja2 template rendering infrastructure."""

from unifi_topology.render._templating import render_template


def test_render_template_markdown_section():
    result = render_template("markdown_section.md.j2", title="Test", body="Hello")
    assert "## Test" in result
    assert "Hello" in result


def test_render_template_device_port_block():
    result = render_template(
        "device_port_block.md.j2",
        device_name="Switch",
        details="details here",
        ports="ports here",
    )
    assert "### Switch" in result
    assert "details here" in result
    assert "ports here" in result


def test_render_template_strict_undefined():
    import pytest
    from jinja2 import UndefinedError

    with pytest.raises(UndefinedError):
        render_template("markdown_section.md.j2", title="Test")
