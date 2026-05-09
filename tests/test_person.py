"""Tests for Person state transitions (E -> I -> R/D) using a stub Disease."""

import pytest

from infectious_disease_simulation.agents.person import Person
from infectious_disease_simulation.display.headless_display import HeadlessDisplay


class StubDisease:
    """Minimal Disease stand-in: every roll returns a preset bool, in order."""

    def __init__(self, infect=False, recover=False, die=False, incubation_time: float = 0.0) -> None:
        self.__infect = infect
        self.__recover = recover
        self.__die = die
        self.__incubation_time = incubation_time

    def infect(self, dt: float) -> bool: return self.__infect
    def recover(self, dt: float) -> bool: return self.__recover
    def die(self, dt: float) -> bool: return self.__die
    def get_incubation_time(self) -> float: return self.__incubation_time


def make_person(status: str = "S",
                disease: StubDisease | None = None,
                incubation_seconds: float = 0.0,
                seconds_per_hour: float = 1.0,
                fps: int = 60) -> Person:
    display = HeadlessDisplay(200, 200, "test")
    return Person(
        display, person_id=0,
        home_location=(0, 0), office_location=(1, 1), home_position=(10, 10),
        home_radius=2, office_radius=2,
        home_to_office_route=[(10, 10), (50, 50)],
        speed=5.0, leave_home=8, status=status,
        disease_obj=disease or StubDisease(),
        incubation_time=incubation_seconds,
        seconds_per_hour=seconds_per_hour,
        delta_time=1 / fps,
    )


class TestStateTransitions:
    def test_exposed_becomes_infected_after_incubation(self) -> None:
        # incubation = 2 seconds, decremented by seconds_per_hour=1 each call
        p = make_person(status="E", incubation_seconds=2.0, seconds_per_hour=1.0)
        p.update_infection_status()
        assert p.get_status() == "E"  # 1s elapsed
        p.update_infection_status()
        assert p.get_status() == "I"  # 2s elapsed - incubation done

    def test_zero_incubation_immediate_infection(self) -> None:
        p = make_person(status="E", incubation_seconds=0.0, seconds_per_hour=1.0)
        p.update_infection_status()
        assert p.get_status() == "I"

    def test_infected_recovers_when_disease_says_so(self) -> None:
        p = make_person(status="I", disease=StubDisease(recover=True))
        p.update_infection_status()
        assert p.get_status() == "R"

    def test_infected_dies_when_recovery_fails_and_die_succeeds(self) -> None:
        p = make_person(status="I", disease=StubDisease(recover=False, die=True))
        p.update_infection_status()
        assert p.get_status() == "D"

    def test_infected_stays_infected_when_neither_fires(self) -> None:
        p = make_person(status="I", disease=StubDisease(recover=False, die=False))
        p.update_infection_status()
        assert p.get_status() == "I"

    def test_recovery_takes_precedence_over_death(self) -> None:
        # If the disease rolls both as True, recovery wins (current code-path order)
        p = make_person(status="I", disease=StubDisease(recover=True, die=True))
        p.update_infection_status()
        assert p.get_status() == "R"

    def test_susceptible_no_change(self) -> None:
        p = make_person(status="S", disease=StubDisease(recover=True, die=True))
        p.update_infection_status()
        assert p.get_status() == "S"

    def test_recovered_no_change(self) -> None:
        p = make_person(status="R", disease=StubDisease(recover=True, die=True))
        p.update_infection_status()
        assert p.get_status() == "R"

    def test_deceased_no_change(self) -> None:
        p = make_person(status="D", disease=StubDisease(recover=True, die=True))
        p.update_infection_status()
        assert p.get_status() == "D"


class TestColours:
    @pytest.mark.parametrize("status,expected", [
        ("S", (144, 238, 144)),
        ("E", (255, 255, 0)),
        ("I", (255, 0, 0)),
        ("R", (204, 153, 255)),
        ("D", (50, 50, 50)),
    ])
    def test_colour_matches_status(self, status: str, expected: tuple[int, int, int]) -> None:
        p = make_person(status=status)
        assert p.get_colour() == expected


class TestMovement:
    def test_movement_advances_along_route(self) -> None:
        # set_office_position inserts home_position at the start of the route, so the
        # first update_position consumes that bookend without physical movement. A few
        # iterations are needed before the person actually steps toward the office.
        p = make_person(status="S")
        p.set_office_position((100, 100))
        p.start_move_to_office()
        start_pos = p.get_current_position()
        for _ in range(5):
            p.update_position()
        assert p.get_current_position() != start_pos

    def test_dead_person_does_not_move(self) -> None:
        p = make_person(status="D")
        p.set_office_position((50, 50))
        p.start_move_to_office()  # No-op for dead person
        start_pos = p.get_current_position()
        p.update_position()
        assert p.get_current_position() == start_pos
