"""Tests for Dijkstra's shortest path on the road-network adjacency list."""

from infectious_disease_simulation.agents.dijkstra import Dijkstra


def test_simple_two_node_path() -> None:
    # A -- 5 -- B
    graph = {
        (0, 0): [((1, 0), 5)],
        (1, 0): [((0, 0), 5)],
    }
    path, weight = Dijkstra(graph).compute((0, 0), (1, 0))
    assert path == [(0, 0), (1, 0)]
    assert weight == 5


def test_picks_shorter_route() -> None:
    # Triangle: direct A-C costs 10, A-B-C costs 3+3=6 (shorter)
    graph = {
        (0, 0): [((10, 0), 10), ((1, 1), 3)],
        (1, 1): [((0, 0), 3), ((10, 0), 3)],
        (10, 0): [((0, 0), 10), ((1, 1), 3)],
    }
    path, weight = Dijkstra(graph).compute((0, 0), (10, 0))
    assert weight == 6
    assert path == [(0, 0), (1, 1), (10, 0)]


def test_unreachable_returns_inf_weight() -> None:
    # Two disconnected components
    graph = {
        (0, 0): [((1, 0), 1)],
        (1, 0): [((0, 0), 1)],
        (5, 5): [((6, 5), 1)],
        (6, 5): [((5, 5), 1)],
    }
    path, weight = Dijkstra(graph).compute((0, 0), (5, 5))
    assert weight == float('inf')
    assert path == []


def test_start_equals_end() -> None:
    graph = {
        (0, 0): [((1, 0), 1)],
        (1, 0): [((0, 0), 1)],
    }
    path, weight = Dijkstra(graph).compute((0, 0), (0, 0))
    assert weight == 0
    assert path == [(0, 0)]


def test_chain_of_nodes() -> None:
    # A-B-C-D-E with weight 1 each; expect total weight 4
    graph = {
        (i, 0): [((i - 1, 0), 1), ((i + 1, 0), 1)]
        for i in range(1, 4)
    }
    graph[(0, 0)] = [((1, 0), 1)]
    graph[(4, 0)] = [((3, 0), 1)]

    path, weight = Dijkstra(graph).compute((0, 0), (4, 0))
    assert weight == 4
    assert path == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
