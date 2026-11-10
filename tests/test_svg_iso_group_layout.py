"""Isometric grouped layout keeps every group's members inside its own block."""

from __future__ import annotations

import pytest

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_layout import _iso_layout_positions
from unifi_topology.render.svg_theme import SvgOptions

_EDGES = [
    Edge("gw", "sw1"),
    Edge("gw", "sw2"),
    Edge("sw1", "a1"),
    Edge("sw2", "a2"),
    Edge("sw1", "b1"),
    Edge("sw2", "b2"),
]
_TYPES = {"gw": "gateway", "sw1": "switch", "sw2": "switch"} | dict.fromkeys(
    ("a1", "a2", "b1", "b2"), "client"
)
_GROUPS = {"LAN": ["gw", "sw1", "sw2"], "IoT": ["a1", "a2"], "Guest": ["b1", "b2"]}


def _gx_ranges(options: SvgOptions, groups: dict[str, list[str]]) -> list[tuple[float, float]]:
    grid = _iso_layout_positions(_EDGES, _TYPES, options, groups, list(groups)).grid_positions
    assert set(grid) == set(_TYPES)
    return [
        (min(grid[node][0] for node in members), max(grid[node][0] for node in members))
        for members in groups.values()
    ]


@pytest.mark.parametrize("compact", [False, True])
def test_grouped_layout_places_groups_in_disjoint_blocks(compact: bool):
    options = SvgOptions(layout_mode="grouped", iso_compact_layout=compact)
    ranges = _gx_ranges(options, _GROUPS)
    for (_, previous_end), (next_start, _) in zip(ranges, ranges[1:]):
        assert next_start > previous_end


def test_grouped_layout_keeps_ungrouped_nodes():
    groups = {"LAN": ["gw", "sw1", "sw2"]}
    options = SvgOptions(layout_mode="grouped")
    grid = _iso_layout_positions(_EDGES, _TYPES, options, groups, None).grid_positions
    lan_end = max(grid[node][0] for node in groups["LAN"])
    assert all(grid[node][0] > lan_end for node in ("a1", "a2", "b1", "b2"))


def test_physical_layout_ignores_groups():
    plain = _iso_layout_positions(_EDGES, _TYPES, SvgOptions())
    with_groups = _iso_layout_positions(_EDGES, _TYPES, SvgOptions(), _GROUPS, None)
    assert plain.grid_positions == with_groups.grid_positions
