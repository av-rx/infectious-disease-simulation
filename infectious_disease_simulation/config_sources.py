"""Pluggable Config providers: GUI (Tkinter) or JSON file."""

import json
import sys
from abc import ABC, abstractmethod

from .config import Config
from .errors import ConfigError


class ConfigSource(ABC):
    """A source that yields a Config (or None if the user cancelled)."""

    @abstractmethod
    def get_config(self) -> Config | None: ...


class GuiConfigSource(ConfigSource):
    """Wraps the Tkinter Interface and bridges it to DB persistence + Config validation."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def get_config(self) -> Config | None:
        # Imported lazily so headless runs don't pay the tkinter import cost
        from .ui.interface import Interface
        from .storage.db_handler import DBHandler

        # Each callback opens its own short-lived DB connection so the UI doesn't have to
        # juggle one — Tkinter's mainloop and a long-lived sqlite cursor don't mix nicely
        # when modal dialogs come and go.
        def fetch_runs_summary() -> list[dict]:
            with DBHandler(self.__db_path) as db:
                return db.fetch_runs_summary()

        def fetch_run(run_id: int) -> dict | None:
            with DBHandler(self.__db_path) as db:
                return db.fetch_run(run_id)

        params = Interface(fetch_runs_summary, fetch_run, Config.from_dict).get_params()
        if params is None:
            return None
        # Already validated inside Interface; this call just rebuilds the typed Config
        return Config.from_dict(params)


class FileConfigSource(ConfigSource):
    """Loads a JSON config file and validates it via Config.from_dict."""

    def __init__(self, path: str) -> None:
        self.__path = path

    def get_config(self) -> Config:
        try:
            with open(self.__path) as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Configuration file not found at: {self.__path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Configuration file is not valid JSON: {e}")
            sys.exit(1)

        try:
            return Config.from_dict(data)
        except ConfigError as e:
            print(f"Invalid configuration: {e}")
            sys.exit(1)
