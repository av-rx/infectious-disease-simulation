"""Validated, immutable simulation parameters."""
from dataclasses import dataclass
from typing import Any
from .errors import ConfigError

@dataclass(frozen=True)
class Config:
    """All parameters that define a single simulation run. Build via `Config.from_dict`."""
    simulation_name: str
    simulation_speed: float
    display_size: int
    num_houses: int
    num_offices: int
    building_size: int
    num_people_in_house: int
    show_drawing: bool
    additional_roads: bool
    infection_rate: float
    incubation_time: float
    recovery_rate: float
    mortality_rate: float

    @staticmethod
    def from_dict(params: dict[str, Any]) -> "Config":
        """Validate a raw param dict and build a Config. Raises ConfigError on any invalid value."""
        try:
            name = str(params["simulation_name"])
            speed = float(params["simulation_speed"])
            ds = int(params["display_size"])
            nh = int(params["num_houses"])
            no = int(params["num_offices"])
            bs = int(params["building_size"])
            ppl = int(params["num_people_in_house"])
            sd = bool(params["show_drawing"])
            ar = bool(params.get("additional_roads", params.get("additional_connections", True)))
            ir = float(params["infection_rate"])
            inc = float(params["incubation_time"])
            rec = float(params["recovery_rate"])
            mort = float(params["mortality_rate"])
        except Exception as e:
            raise ConfigError(f"Invalid configuration: {e}")

        if not name:
            raise ConfigError("simulation_name must not be empty.")
        if len(name) > 50:
            raise ConfigError("simulation_name is too long (max 50 characters).")
        if speed <= 0:
            raise ConfigError(f"'{speed}'. simulation_speed must be positive.")
        if ds <= 0:
            raise ConfigError(f"'{ds}'. display_size must be a positive integer.")
        if ds > 2160:  # 4K display height — beyond this, windows don't fit on common monitors
            raise ConfigError(f"'{ds}'. display_size too large (max 2160).")
        if not (0 <= ir <= 1):
            raise ConfigError(f"'{ir}', infection_rate must be between 0 and 1.")
        if inc < 0:
            raise ConfigError(f"'{inc}'. incubation_time must be non-negative.")
        if not (0 <= rec <= 1):
            raise ConfigError(f"'{rec}'. recovery_rate must be between 0 and 1.")
        if not (0 <= mort <= 1):
            raise ConfigError(f"'{mort}'. mortality_rate must be between 0 and 1.")
        if bs <= 0:
            raise ConfigError(f"'{bs}'. building_size must be a positive integer.")
        if nh <= 0 or no <= 0:
            raise ConfigError("There must be at least one house and one office.")
        if nh + no > (ds // bs) ** 2:
            raise ConfigError("Number of buildings exceeds the number of possible locations.")
        if ppl <= 0:
            raise ConfigError(f"'{ppl}'. num_people_in_house must be a positive integer.")

        return Config(simulation_name=name,
                      simulation_speed=speed,
                      display_size=ds,
                      num_houses=nh,
                      num_offices=no,
                      building_size=bs,
                      num_people_in_house=ppl,
                      show_drawing=sd,
                      additional_roads=ar,
                      infection_rate=ir,
                      incubation_time=inc,
                      recovery_rate=rec,
                      mortality_rate=mort)