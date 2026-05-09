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
    """Wraps the Tkinter Interface to collect parameters interactively."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def get_config(self) -> Config | None:
        # Imported lazily so headless runs don't pay the tkinter import cost
        from .ui.interface import Interface
        return Interface(self.__db_path).get_config()


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
