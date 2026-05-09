"""Tests for the heap-based PriorityQueue used by Dijkstra."""

import pytest

from infectious_disease_simulation.agents.dijkstra import PriorityQueue


def test_pop_returns_lowest_priority_item() -> None:
    pq = PriorityQueue()
    pq.insert_item((1, 1), priority=5)
    pq.insert_item((2, 2), priority=1)
    pq.insert_item((3, 3), priority=3)
    assert pq.pop_item() == (2, 2)
    assert pq.pop_item() == (3, 3)
    assert pq.pop_item() == (1, 1)


def test_is_empty() -> None:
    pq = PriorityQueue()
    assert pq.is_empty() is True
    pq.insert_item((0, 0), priority=1)
    assert pq.is_empty() is False
    pq.pop_item()
    assert pq.is_empty() is True


def test_pop_from_empty_raises() -> None:
    pq = PriorityQueue()
    with pytest.raises(IndexError):
        pq.pop_item()


def test_heap_invariant_after_many_inserts() -> None:
    """Insert priorities in pseudo-random order, pop them all, check sorted output."""
    pq = PriorityQueue()
    priorities = [9, 4, 7, 1, 5, 2, 8, 3, 6, 0]
    for i, p in enumerate(priorities):
        pq.insert_item((i, i), priority=p)

    popped_priorities = []
    items_popped = 0
    while not pq.is_empty():
        # The PQ doesn't expose priority on pop; reconstruct from item id
        item = pq.pop_item()
        popped_priorities.append(priorities[item[0]])
        items_popped += 1

    assert items_popped == len(priorities)
    assert popped_priorities == sorted(priorities)


def test_single_element() -> None:
    pq = PriorityQueue()
    pq.insert_item((42, 42), priority=99)
    assert pq.pop_item() == (42, 42)
    assert pq.is_empty() is True
