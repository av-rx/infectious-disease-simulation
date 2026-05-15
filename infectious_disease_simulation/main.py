"""Entry point: parse args, source a Config, persist it, run the simulation."""

import random
import sys
import warnings

# pygame 2.x uses the deprecated pkg_resources API internally; suppress the noise.
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

from .cli import parse_args
from .config_sources import FileConfigSource, GuiConfigSource
from .display import Display
from .errors import DBError, UsageError
from .paths import resolve_db_path
from .runner import SimulationRunner
from .storage.db_handler import DBHandler


def main() -> None:
    try:
        args = parse_args(sys.argv[1:])
    except UsageError as e:
        print(e)
        sys.exit(2)

    db_path = resolve_db_path()

    source = FileConfigSource(args.config_path) if args.headless else GuiConfigSource(db_path)
    config = source.get_config()
    if config is None:
        return  # User closed the GUI without submitting

    try:
        with DBHandler(db_path) as db:
            db.save_params(config)
        print("Parameters saved successfully.")
    except DBError as e:
        print(f"Error while saving parameters: {e}")

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    if args.seed is not None:
        print(f"Using seed: {args.seed}")

    display = Display(config.display_size, config.display_size,
                      config.simulation_name, args.headless)
    SimulationRunner(config, display, rng=rng, seed=args.seed).run()


if __name__ == "__main__":
    main()
