"""End-to-end smoke test: a full headless simulation completes deterministically.

This is the regression net for any future structural change. It uses a deliberately
small config so the test runs in well under a second.
"""

import random

from infectious_disease_simulation.config import Config
from infectious_disease_simulation.display.headless_display import HeadlessDisplay
from infectious_disease_simulation.runner import SimulationRunner


SMALL_CONFIG = {
    "simulation_name": "smoke",
    "simulation_speed": 5.0,
    "display_size": 400,
    "num_houses": 8,
    "num_offices": 2,
    "building_size": 50,
    "num_people_in_house": 3,
    "show_drawing": False,
    "additional_roads": True,
    "infection_rate": 0.7,
    "incubation_time": 1.0,
    "recovery_rate": 0.5,
    "mortality_rate": 0.1,
}


def run_with_seed(seed: int) -> dict[str, int]:
    """Run a complete headless simulation with the given seed, return final S/E/I/R/D counts."""
    config = Config.from_dict(SMALL_CONFIG)
    display = HeadlessDisplay(config.display_size, config.display_size, config.simulation_name)
    rng = random.Random(seed)
    runner = SimulationRunner(config, display, rng=rng, seed=seed)
    runner.run()
    # Reach into the runner via name-mangling to grab the final population state.
    # Slightly hacky but avoids exposing __population publicly just for tests.
    population = runner._SimulationRunner__population  # type: ignore[attr-defined]
    return population.get_status_counts()


def test_smoke_run_completes() -> None:
    counts = run_with_seed(42)
    # Every person ends in S, R, or D (no active E/I once the loop terminates)
    assert counts["E"] == 0
    assert counts["I"] == 0
    total = sum(counts.values())
    expected_total = SMALL_CONFIG["num_houses"] * SMALL_CONFIG["num_people_in_house"]
    assert total == expected_total


def test_smoke_run_is_deterministic() -> None:
    """Same seed twice -> identical final state."""
    counts_a = run_with_seed(42)
    counts_b = run_with_seed(42)
    assert counts_a == counts_b


def test_different_seeds_can_produce_different_results() -> None:
    """Two arbitrary seeds shouldn't be guaranteed to match.

    Sanity check that the seed actually drives the trajectory; if these always agreed,
    something would be ignoring the seed entirely.
    """
    counts_a = run_with_seed(1)
    counts_b = run_with_seed(2)
    counts_c = run_with_seed(3)
    # At least one pair should differ. If all three match exactly, the seed isn't doing anything.
    assert not (counts_a == counts_b == counts_c)
