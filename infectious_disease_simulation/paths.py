"""Filesystem locations used by the program (currently just the SQLite DB path)."""

import os


def resolve_db_path(db_name: str = "simulation_params.db") -> str:
    """Resolve the DB path under $XDG_DATA_HOME (or ~/.local/share), falling back to cwd on failure."""
    # Logic adapted from pyxdg: https://cgit.freedesktop.org/xdg/pyxdg/tree/xdg/BaseDirectory.py
    home = os.path.expanduser('~')
    xdg_data_home = os.environ.get('XDG_DATA_HOME') or os.path.join(home, '.local', 'share')
    dir_path = os.path.join(xdg_data_home, "infectious-disease-simulation")

    try:
        os.makedirs(dir_path, exist_ok=True)
    except OSError as err:
        print(f"Could not create data dir, using current directory: {err}")
        dir_path = os.path.curdir

    return os.path.join(dir_path, db_name)
