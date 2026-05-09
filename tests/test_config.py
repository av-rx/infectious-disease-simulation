"""Tests for Config.from_dict input validation."""

import pytest

from infectious_disease_simulation.config import Config
from infectious_disease_simulation.errors import ConfigError


def make_params(**overrides) -> dict:
    """A known-valid params dict with optional field overrides."""
    base = {
        "simulation_name": "Test",
        "simulation_speed": 2.0,
        "display_size": 400,
        "num_houses": 4,
        "num_offices": 2,
        "building_size": 50,
        "num_people_in_house": 2,
        "show_drawing": False,
        "additional_roads": False,
        "infection_rate": 0.5,
        "incubation_time": 1.0,
        "recovery_rate": 0.5,
        "mortality_rate": 0.1,
    }
    base.update(overrides)
    return base


class TestValidParams:
    def test_round_trip(self) -> None:
        c = Config.from_dict(make_params())
        assert c.simulation_name == "Test"
        assert c.simulation_speed == 2.0
        assert c.num_houses == 4
        assert c.additional_roads is False

    def test_additional_connections_legacy_key(self) -> None:
        # Old DB rows use `additional_connections` instead of `additional_roads`
        params = make_params()
        del params["additional_roads"]
        params["additional_connections"] = True
        c = Config.from_dict(params)
        assert c.additional_roads is True

    def test_zero_rates_allowed(self) -> None:
        # 0 is a valid endpoint for rates
        c = Config.from_dict(make_params(infection_rate=0, recovery_rate=0, mortality_rate=0))
        assert c.infection_rate == 0
        assert c.recovery_rate == 0
        assert c.mortality_rate == 0

    def test_one_rates_allowed(self) -> None:
        c = Config.from_dict(make_params(infection_rate=1, recovery_rate=1, mortality_rate=1))
        assert c.infection_rate == 1


class TestNameValidation:
    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ConfigError, match="empty"):
            Config.from_dict(make_params(simulation_name=""))

    def test_too_long_name_rejected(self) -> None:
        with pytest.raises(ConfigError, match="too long"):
            Config.from_dict(make_params(simulation_name="x" * 51))

    def test_50_chars_allowed(self) -> None:
        Config.from_dict(make_params(simulation_name="x" * 50))


class TestNumericBounds:
    @pytest.mark.parametrize("speed", [0, -1, -0.001])
    def test_non_positive_speed_rejected(self, speed: float) -> None:
        with pytest.raises(ConfigError, match="simulation_speed"):
            Config.from_dict(make_params(simulation_speed=speed))

    @pytest.mark.parametrize("size", [0, -100])
    def test_non_positive_display_size_rejected(self, size: int) -> None:
        with pytest.raises(ConfigError, match="display_size"):
            Config.from_dict(make_params(display_size=size))

    def test_oversize_display_rejected(self) -> None:
        with pytest.raises(ConfigError, match="display_size"):
            Config.from_dict(make_params(display_size=2161))

    def test_4k_display_allowed(self) -> None:
        Config.from_dict(make_params(display_size=2160, num_houses=2, num_offices=2,
                                     building_size=400))

    @pytest.mark.parametrize("rate", [-0.1, 1.1, 2.0])
    def test_infection_rate_out_of_range(self, rate: float) -> None:
        with pytest.raises(ConfigError, match="infection_rate"):
            Config.from_dict(make_params(infection_rate=rate))

    @pytest.mark.parametrize("rate", [-0.1, 1.1])
    def test_recovery_rate_out_of_range(self, rate: float) -> None:
        with pytest.raises(ConfigError, match="recovery_rate"):
            Config.from_dict(make_params(recovery_rate=rate))

    @pytest.mark.parametrize("rate", [-0.1, 1.1])
    def test_mortality_rate_out_of_range(self, rate: float) -> None:
        with pytest.raises(ConfigError, match="mortality_rate"):
            Config.from_dict(make_params(mortality_rate=rate))

    def test_negative_incubation_rejected(self) -> None:
        with pytest.raises(ConfigError, match="incubation_time"):
            Config.from_dict(make_params(incubation_time=-0.5))

    def test_zero_incubation_allowed(self) -> None:
        Config.from_dict(make_params(incubation_time=0))

    @pytest.mark.parametrize("size", [0, -10])
    def test_non_positive_building_size_rejected(self, size: int) -> None:
        with pytest.raises(ConfigError, match="building_size"):
            Config.from_dict(make_params(building_size=size))


class TestBuildingPlacement:
    def test_zero_houses_rejected(self) -> None:
        with pytest.raises(ConfigError, match="house and one office"):
            Config.from_dict(make_params(num_houses=0))

    def test_zero_offices_rejected(self) -> None:
        with pytest.raises(ConfigError, match="house and one office"):
            Config.from_dict(make_params(num_offices=0))

    def test_too_many_buildings_for_grid(self) -> None:
        # 400/50 = 8 tiles per side -> 64 cells. Asking for 100 buildings shouldn't fit.
        with pytest.raises(ConfigError, match="exceeds the number of possible locations"):
            Config.from_dict(make_params(num_houses=80, num_offices=20))

    def test_exact_fit_allowed(self) -> None:
        # 64 cells, 64 buildings -> fits exactly
        Config.from_dict(make_params(num_houses=63, num_offices=1))


class TestPopulation:
    @pytest.mark.parametrize("ppl", [0, -1])
    def test_non_positive_people_per_house_rejected(self, ppl: int) -> None:
        with pytest.raises(ConfigError, match="num_people_in_house"):
            Config.from_dict(make_params(num_people_in_house=ppl))


class TestStructuralErrors:
    def test_missing_field_raises_config_error(self) -> None:
        params = make_params()
        del params["infection_rate"]
        with pytest.raises(ConfigError, match="Invalid configuration"):
            Config.from_dict(params)

    def test_uncastable_value_raises_config_error(self) -> None:
        with pytest.raises(ConfigError, match="Invalid configuration"):
            Config.from_dict(make_params(num_houses="not a number"))


class TestImmutability:
    def test_config_is_frozen(self) -> None:
        c = Config.from_dict(make_params())
        with pytest.raises(Exception):  # FrozenInstanceError in 3.11+
            c.simulation_name = "Other"  # type: ignore[misc]
