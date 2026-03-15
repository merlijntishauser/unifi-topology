"""Public API export and signature contract tests."""

from __future__ import annotations

import inspect

import unifi_topology as ut


def test_top_level_exports_resolve():
    for name in ut.__all__:
        assert hasattr(ut, name), name
        assert getattr(ut, name) is not None, name


def test_public_topology_signature_stays_compatible():
    signature = inspect.signature(ut.build_topology)
    parameters = list(signature.parameters.values())

    assert [parameter.name for parameter in parameters] == [
        "devices",
        "include_ports",
        "only_unifi",
        "gateways",
    ]
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters[1:])


def test_public_render_signatures_stay_compatible():
    render_svg_signature = inspect.signature(ut.render_svg)
    render_svg_parameters = list(render_svg_signature.parameters.values())
    assert render_svg_parameters[0].name == "edges"
    assert render_svg_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert render_svg_parameters[1].name == "node_types"
    assert render_svg_parameters[1].kind is inspect.Parameter.KEYWORD_ONLY

    render_dual_signature = inspect.signature(ut.render_dual)
    render_dual_parameters = list(render_dual_signature.parameters.values())
    assert render_dual_parameters[0].name == "edges"
    assert render_dual_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert render_dual_parameters[1].name == "node_types"
    assert render_dual_parameters[1].kind is inspect.Parameter.KEYWORD_ONLY


def test_topology_result_fields_stay_public():
    fields = ut.TopologyResult.__dataclass_fields__
    assert "raw_edges" in fields
    assert "tree_edges" in fields
