"""Shared pytest fixtures."""

import random

import pytest

from infectious_disease_simulation.display.headless_display import HeadlessDisplay


@pytest.fixture
def rng() -> random.Random:
    """A fixed-seed RNG so any test using it is deterministic."""
    return random.Random(42)


@pytest.fixture
def headless_display() -> HeadlessDisplay:
    """A small headless display surface, sufficient for any code path that touches a Surface."""
    return HeadlessDisplay(400, 400, "test")
