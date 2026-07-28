"""Isometric edges must route around nodes, not across them.

Every leg runs along a grid axis, so each projects to a true isometric line. What
the routing chooses is which axis to travel first, and whether to step sideways
into a clear lane before turning.
"""

from __future__ import annotations

import pytest

from unifi_topology.render._svg_iso_routing import edge_route, occupied_cells, route_corners

pytestmark = pytest.mark.unit


def _legs(src: tuple[int, int], dst: tuple[int, int], occupied) -> list[tuple]:
    corners = [(int(x), int(y)) for x, y in route_corners(*src, *dst, occupied)]
    points = [src, *corners, dst]
    return list(zip(points, points[1:], strict=False))


def _crossed(src, dst, occupied) -> set[tuple[int, int]]:
    """Cells the route passes over, excluding its own endpoints."""
    seen: set[tuple[int, int]] = set()
    for (x0, y0), (x1, y1) in _legs(src, dst, occupied):
        step_x = (x1 > x0) - (x1 < x0)
        step_y = (y1 > y0) - (y1 < y0)
        x, y = x0, y0
        while (x, y) != (x1, y1):
            x, y = x + step_x, y + step_y
            seen.add((x, y))
    return seen - {src, dst}


def test_every_leg_runs_along_a_grid_axis():
    """A leg that is not axis-aligned would not project to an isometric line."""
    for (x0, y0), (x1, y1) in _legs((0, 0), (6, 4), frozenset()):
        assert x0 == x1 or y0 == y1


def test_a_clear_route_uses_a_single_corner():
    corners = route_corners(0, 0, 6, 4, frozenset())
    assert len(corners) == 1


def test_the_route_avoids_a_blocked_lane():
    """One L crosses the obstacle, the other does not."""
    blocked = frozenset({(6, 0)})  # sits on the along-x-first corner
    assert (6, 0) not in _crossed((0, 0), (6, 4), blocked)


def test_a_three_segment_route_is_used_when_both_l_shapes_are_blocked():
    blocked = frozenset({(6, 0), (0, 4)})  # both corners occupied
    corners = route_corners(0, 0, 6, 4, blocked)
    assert len(corners) == 2
    assert not (_crossed((0, 0), (6, 4), blocked) & blocked)


def test_a_route_around_a_wall_crosses_nothing():
    wall = frozenset({(3, y) for y in range(0, 5)} - {(3, 4)})
    assert not (_crossed((0, 0), (6, 4), wall) & wall)


def test_endpoints_do_not_count_as_obstacles():
    occupied = frozenset({(0, 0), (6, 4)})
    assert route_corners(0, 0, 6, 4, occupied) == route_corners(0, 0, 6, 4, frozenset())


def test_routing_is_deterministic():
    blocked = frozenset({(6, 0), (0, 4), (3, 2)})
    assert route_corners(0, 0, 6, 4, blocked) == route_corners(0, 0, 6, 4, blocked)


def test_occupied_cells_rounds_grid_positions():
    assert occupied_cells({"a": (2.0, -4.0), "b": (0.4, 0.6)}) == frozenset({(2, -4), (0, 1)})


def test_a_dense_field_still_yields_a_clear_route():
    """The case from the live topology: blocks of clients between two switches."""
    occupied = frozenset({(x, y) for x in range(2, 9, 2) for y in range(2, 9, 2)})
    assert not (_crossed((0, 0), (10, 10), occupied) & occupied)


class TestOptIn:
    """Routing is opt-in; the default must keep drawing what it always did."""

    @staticmethod
    def _edge_paths(**option_kwargs) -> list[str]:
        import re

        from unifi_topology import render_svg_isometric
        from unifi_topology.model.topology import Edge
        from unifi_topology.render.svg_theme import SvgOptions

        edges = [
            Edge(left="gw", right="sw"),
            Edge(left="sw", right="ap"),
            Edge(left="sw", right="c1"),
            Edge(left="sw", right="c2"),
            Edge(left="ap", right="c3"),
        ]
        types = {
            "gw": "gateway",
            "sw": "switch",
            "ap": "ap",
            "c1": "client",
            "c2": "client",
            "c3": "client",
        }
        svg = render_svg_isometric(edges, node_types=types, options=SvgOptions(**option_kwargs))
        return re.findall(r'<path d="(M [^"]+)"', svg)

    def test_default_is_unchanged(self):
        """Equivalent to always turning on the gx axis, as before the option existed."""
        assert self._edge_paths() == self._edge_paths(iso_route_around_nodes=False)

    def test_the_option_changes_routing(self):
        plain = self._edge_paths()
        routed = self._edge_paths(iso_route_around_nodes=True, iso_compact_layout=True)
        assert plain != routed

    def test_empty_occupancy_reproduces_the_original_corner(self):
        """The flag-off path relies on this: no obstacles means the first candidate."""
        assert route_corners(0, 0, 6, 4, frozenset()) == [(6.0, 0.0)]


class TestEdgeRoute:
    """The final lane of an edge, escapes and fan separation included."""

    @staticmethod
    def _clearance(points, occupied, endpoints):
        """Smallest grid distance from any sampled leg point to an occupied cell."""
        best = 99.0
        cells = occupied - {tuple(map(int, e)) for e in endpoints}
        for (ax, ay), (bx, by) in zip(points, points[1:], strict=False):
            for i in range(1, 40):
                x, y = ax + (bx - ax) * i / 40, ay + (by - ay) * i / 40
                for cx, cy in cells:
                    best = min(best, abs(x - cx) + abs(y - cy))
        return best

    def test_a_clear_edge_is_untouched(self):
        assert edge_route((0, 0), (6, 4), frozenset()) == [(0, 0), (6.0, 0.0), (6, 4)]

    def test_a_blocked_straight_run_escapes_to_the_half_lane(self):
        occupied = frozenset({(0, 0), (4, 0), (8, 0)})
        points = edge_route((0, 0), (8, 0), occupied)
        assert points[0] == (0, 0) and points[-1] == (8, 0)
        assert self._clearance(points, occupied, [(0, 0), (8, 0)]) >= 0.45

    def test_a_fully_blocked_bent_route_escapes(self):
        """Both L corners and every Z lane can cross something; the half-lane
        shift cannot, because no node cell has fractional coordinates."""
        occupied = frozenset(
            {(0, 0), (16, -4)} | {(x, y) for x in range(2, 15, 2) for y in (-4, -2, 0)}
        )
        points = edge_route((0, 0), (16, -4), occupied)
        assert points[0] == (0, 0) and points[-1] == (16, -4)
        assert self._clearance(points, occupied, [(0, 0), (16, -4)]) >= 0.45

    def test_every_leg_stays_grid_aligned_even_when_escaped(self):
        occupied = frozenset({(4, 0)})
        for a, b in zip(
            *(lambda p: (p, p[1:]))(edge_route((0, 0), (8, 0), occupied)), strict=False
        ):
            assert abs(a[0] - b[0]) < 1e-9 or abs(a[1] - b[1]) < 1e-9

    def test_lane_offsets_separate_a_fan(self):
        from unifi_topology.model.topology import Edge
        from unifi_topology.render._svg_iso_routing import edge_lane_offsets

        edges = [Edge("hub", f"c{i}") for i in range(4)] + [Edge("other", "x")]
        offsets = edge_lane_offsets(edges)
        assert len(set(offsets[:4])) == 4, "fan edges share a lane"
        assert offsets[4] == 0.0, "a lone edge needs no offset"

    def test_offset_paths_keep_their_endpoints(self):
        from unifi_topology.render._svg_iso_routing import offset_route

        points = offset_route((0, 0), [(6.0, 0.0)], (6, 4), 0.3)
        assert points[0] == (0, 0) and points[-1] == (6, 4)

    def test_escape_lanes_stay_clear_of_integer_lanes(self):
        """0.5 plus a compressed fan offset must never reach a whole lane."""
        from unifi_topology.render._svg_iso_routing import _OFFSET_CYCLE

        for offset in _OFFSET_CYCLE:
            shift = 0.5 + offset * 0.25
            assert 0.3 <= shift <= 0.7
