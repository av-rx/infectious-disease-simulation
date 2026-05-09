"""Command-line argument parsing for the simulation entry point."""

import argparse
from dataclasses import dataclass

from .errors import UsageError


@dataclass(frozen=True)
class CliArgs:
    headless: bool
    config_path: str | None
    seed: int | None


def parse_args(argv: list[str]) -> CliArgs:
    """Parse argv into CliArgs. Raises UsageError on invalid combinations."""
    parser = argparse.ArgumentParser(
        prog="infectious-disease-simulation",
        description="Run a procedurally generated SEIRD infectious-disease simulation.",
    )
    parser.add_argument("--headless", action="store_true",
                        help="Run without a GUI. Requires a config file path.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Optional integer seed for deterministic runs (building placement, "
                             "office assignment, disease rolls).")
    parser.add_argument("config", nargs="?",
                        help="Path to a JSON config file (only used with --headless).")

    ns = parser.parse_args(argv)

    if ns.headless and ns.config is None:
        raise UsageError("--headless requires a config file path: --headless <config_file_path>")
    if not ns.headless and ns.config is not None:
        raise UsageError("Positional config path is only valid with --headless.")

    return CliArgs(headless=ns.headless, config_path=ns.config, seed=ns.seed)
