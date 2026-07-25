"""The compact isometric layout must pack densely without stacking nodes."""

from __future__ import annotations

import math

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_district_layout import _iso_district_grid
from unifi_topology.render._svg_iso_layout import _iso_layout_positions
from unifi_topology.render.svg_theme import SvgOptions


def _star(hub: str, count: int, prefix: str = "c") -> list[Edge]:
    return [Edge(left=hub, right=f"{prefix}{i}") for i in range(count)]


def _types(edges: list[Edge], hub_type: str = "switch") -> dict[str, str]:
    types = {edge.right: "client" for edge in edges}
    types.update({edge.left: hub_type for edge in edges})
    return types


def _grid(edges: list[Edge]) -> dict[str, tuple[float, float]]:
    return _iso_district_grid(edges, _types(edges))


def test_every_node_gets_its_own_cell():
    """The tree layout averages child indices, which lets parents collide."""
    edges = _star("sw", 40)
    grid = _grid(edges)
    assert len(set(grid.values())) == len(grid)


def test_shared_child_does_not_stack_its_parents():
    """Two switches feeding one client previously landed on the same tile."""
    edges = [Edge(left="gw", right="shared"), Edge(left="sw", right="shared")]
    types = {"gw": "gateway", "sw": "switch", "shared": "client"}
    grid = _iso_district_grid(edges, types)
    assert len(set(grid.values())) == len(grid) == 3


def test_all_nodes_are_placed():
    edges = _star("sw", 25) + [Edge(left="gw", right="sw")]
    grid = _grid(edges)
    assert set(grid) == {"gw", "sw"} | {f"c{i}" for i in range(25)}


def test_disconnected_nodes_are_still_placed():
    edges = _star("sw", 3)
    types = _types(edges) | {"lonely": "iot"}
    grid = _iso_district_grid(edges, types)
    assert "lonely" in grid


def test_layout_is_deterministic():
    edges = _star("sw", 30)
    assert _grid(edges) == _grid(edges)


def test_empty_topology_is_handled():
    assert _iso_district_grid([], {}) == {}


def _screen_extent(edges: list[Edge], options: SvgOptions) -> tuple[float, float, int]:
    placed = _iso_layout_positions(edges, _types(edges), options)
    xs = [x for x, _y in placed.positions.values()]
    ys = [y for _x, y in placed.positions.values()]
    return max(xs) - min(xs), max(ys) - min(ys), len(placed.positions)


def test_compact_layout_is_far_denser_than_the_diagonal_default():
    """The default layout puts N siblings on one diagonal; this must not."""
    edges = _star("sw", 60)
    wide, tall, count = _screen_extent(edges, SvgOptions())
    c_wide, c_tall, c_count = _screen_extent(edges, SvgOptions(iso_compact_layout=True))
    assert count == c_count
    assert c_wide * c_tall < (wide * tall) / 4


def test_compact_layout_avoids_extreme_aspect_ratios():
    edges = _star("sw", 60)
    wide, tall, _count = _screen_extent(edges, SvgOptions(iso_compact_layout=True))
    assert 0.5 < (wide / tall) < 4.0


def test_large_hub_spreads_sideways_rather_than_forming_a_tower():
    """A switch with many clients should widen, not grow an endless column."""
    grid = _grid(_star("sw", 60))
    spines = {(gx + gy) / 2 for gx, gy in grid.values()}
    laterals = {(gx - gy) / 2 for gx, gy in grid.values()}
    assert len(laterals) > 1
    assert len(spines) <= 60


def test_grid_coordinates_stay_on_the_isometric_lattice():
    """gx and gy must share parity, or tiles land between lattice cells."""
    for gx, gy in _grid(_star("sw", 20)).values():
        assert float(gx).is_integer() and float(gy).is_integer()
        assert (gx + gy) % 2 == 0


def test_default_layout_is_unchanged_by_the_flag():
    edges = _star("sw", 12)
    default = _iso_layout_positions(edges, _types(edges), SvgOptions())
    compact = _iso_layout_positions(edges, _types(edges), SvgOptions(iso_compact_layout=True))
    assert default.positions != compact.positions
    assert not math.isclose(default.width, compact.width)
