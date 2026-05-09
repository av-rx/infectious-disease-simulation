"""Tests for the MST + additional-connections layer."""

import numpy as np

from infectious_disease_simulation.world.graph.mst import MST


def make_map(building_coords: list[tuple[int, int]], shape: tuple[int, int] = (10, 10)) -> np.ndarray:
    """Build a tilemap with `1` at every (col, row) in `building_coords`, 0 elsewhere."""
    arr = np.zeros(shape, dtype=int)
    for col, row in building_coords:
        # Tilemap stores [row, col] (numpy convention) with map[y, x] indexing
        arr[row, col] = 1
    return arr


def test_mst_connects_two_buildings() -> None:
    arr = make_map([(0, 0), (5, 0)])
    mst = MST(arr).get_mst(additional_roads=False)
    # Both nodes should appear and be each other's neighbour
    assert (0, 0) in mst
    assert (5, 0) in mst
    neighbours_of_first = [n for n, _ in mst[(0, 0)]]
    assert (5, 0) in neighbours_of_first


def test_mst_spans_a_small_cluster() -> None:
    # 4 buildings clustered closely - all should land in one connected component
    arr = make_map([(0, 0), (0, 1), (1, 0), (1, 1)])
    mst = MST(arr).get_mst(additional_roads=False)

    # An MST over 4 nodes has 3 edges. Each edge is double-counted (one per endpoint),
    # so the sum of len(neighbours) should be 6.
    total_edges = sum(len(neighbours) for neighbours in mst.values())
    assert total_edges == 6

    # And the MST should be connected (BFS reaches all nodes from any start)
    visited: set[tuple[int, int]] = set()
    stack = [next(iter(mst))]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for neighbour, _ in mst[node]:
            stack.append(neighbour)
    assert visited == set(mst.keys())


def test_additional_roads_adds_edges() -> None:
    # A linear 5-building configuration where additional_connections may add edges
    # between leaf nodes (length 4 line: 5 nodes, 4 MST edges).
    arr = make_map([(0, 0), (3, 0), (6, 0), (9, 0), (9, 4)], shape=(10, 12))

    mst_only = MST(arr).get_mst(additional_roads=False)
    mst_with_extras = MST(arr).get_mst(additional_roads=True)

    edges_only = sum(len(n) for n in mst_only.values()) // 2
    edges_with_extras = sum(len(n) for n in mst_with_extras.values()) // 2

    # additional_roads either adds an edge or makes no change; never removes one.
    assert edges_with_extras >= edges_only
