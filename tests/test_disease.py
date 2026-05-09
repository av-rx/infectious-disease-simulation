"""Tests for the per-real-second hazard model in Disease."""

import math
import random

import pytest

from infectious_disease_simulation.simulation.disease import Disease


SECONDS_PER_HOUR = 0.5  # arbitrary; only the lambda calc cares


def make_disease(infection: float = 0.5, incubation: float = 2.0,
                 recovery: float = 0.5, mortality: float = 0.1,
                 rng: random.Random | None = None) -> Disease:
    return Disease(infection, incubation, recovery, mortality, SECONDS_PER_HOUR, rng=rng)


class TestEndpoints:
    """Probability 0 should never fire; probability 1 should always fire."""

    def test_zero_infection_never_fires(self) -> None:
        d = make_disease(infection=0)
        # Even with absurdly long delta_time, hazard is 0 -> never True
        assert d.infect(1e9) is False

    def test_zero_recovery_never_fires(self) -> None:
        d = make_disease(recovery=0)
        assert d.recover(1e9) is False

    def test_zero_mortality_never_fires(self) -> None:
        d = make_disease(mortality=0)
        assert d.die(1e9) is False

    def test_one_infection_always_fires_with_positive_dt(self) -> None:
        d = make_disease(infection=1)
        assert d.infect(0.001) is True

    def test_one_infection_does_not_fire_at_zero_dt(self) -> None:
        d = make_disease(infection=1)
        # delta_time of 0 should not trigger the event even at p=1
        assert d.infect(0) is False


class TestDeterminism:
    """Two Disease instances with identical seed and identical inputs must produce identical rolls."""

    def test_same_seed_same_rolls(self) -> None:
        d1 = make_disease(rng=random.Random(123))
        d2 = make_disease(rng=random.Random(123))
        rolls1 = [d1.infect(0.01) for _ in range(50)]
        rolls2 = [d2.infect(0.01) for _ in range(50)]
        assert rolls1 == rolls2

    def test_different_seeds_diverge(self) -> None:
        # Use a large enough dt that per-roll probability is meaningful (~40%) so the
        # bool sequences actually vary between seeds. Tiny dt -> all False under any seed.
        d1 = make_disease(rng=random.Random(1))
        d2 = make_disease(rng=random.Random(2))
        rolls1 = [d1.infect(10) for _ in range(50)]
        rolls2 = [d2.infect(10) for _ in range(50)]
        assert rolls1 != rolls2


class TestStatistical:
    """Over many trials the empirical frequency should approach the theoretical hazard probability."""

    def test_infection_frequency_matches_hazard(self) -> None:
        # p_day = 0.5 over (24 * seconds_per_hour) seconds; check small dt fires roughly
        # 1 - exp(-lambda * dt) of the time
        rng = random.Random(7)
        d = make_disease(infection=0.5, rng=rng)
        # Per-second hazard solved from p_day = 0.5
        lambda_per_sec = -math.log(0.5) / (24 * SECONDS_PER_HOUR)
        dt = 0.1
        expected = 1.0 - math.exp(-lambda_per_sec * dt)

        trials = 50_000
        hits = sum(d.infect(dt) for _ in range(trials))
        empirical = hits / trials
        # 4-sigma is ample for this trial count
        sigma = math.sqrt(expected * (1 - expected) / trials)
        assert abs(empirical - expected) < 4 * sigma


class TestIncubation:
    def test_incubation_time_converted_to_real_seconds(self) -> None:
        # 2 days * 24 hours/day * SECONDS_PER_HOUR real seconds
        d = make_disease(incubation=2.0)
        assert d.get_incubation_time() == pytest.approx(2 * 24 * SECONDS_PER_HOUR)

    def test_zero_incubation(self) -> None:
        d = make_disease(incubation=0)
        assert d.get_incubation_time() == 0
