"""SQLite handler for persisting and loading simulation run parameters."""

import sqlite3
from typing import Optional
from datetime import datetime
from ..config import Config
from ..errors import DBError


class DBHandler:
    """Context manager wrapping a SQLite connection for the `simulations` table."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "DBHandler":
        try:
            self.conn = sqlite3.connect(self.path, timeout=30)
            self._create_table()
            return self
        except sqlite3.Error as e:
            raise DBError(f"Database connection error: {e}")

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_table(self) -> None:
        """Create the `simulations` table if it doesn't already exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS simulations (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            simulation_name TEXT NOT NULL,
            simulation_speed REAL NOT NULL,
            display_size INTEGER NOT NULL,
            num_houses INTEGER NOT NULL,
            num_offices INTEGER NOT NULL,
            building_size INTEGER NOT NULL,
            num_people_in_house INTEGER NOT NULL,
            show_drawing INTEGER NOT NULL,
            additional_roads INTEGER NOT NULL,
            infection_rate REAL NOT NULL,
            incubation_time REAL NOT NULL,
            recovery_rate REAL NOT NULL,
            mortality_rate REAL NOT NULL
        );
        """
        try:
            assert self.conn is not None
            cur = self.conn.cursor()
            cur.execute(create_table_query)
            self.conn.commit()
        except sqlite3.Error as e:
            raise DBError(f"Error creating table: {e}")

    def save_params(self, config: Config) -> int:
        """Persist a Config and return its new run_id."""
        insert = """
        INSERT INTO simulations (
            datetime, simulation_name, simulation_speed, display_size,
            num_houses, num_offices, building_size, num_people_in_house,
            show_drawing, additional_roads,
            infection_rate, incubation_time, recovery_rate, mortality_rate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            assert self.conn is not None
            cur = self.conn.cursor()
            cur.execute(
                insert,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    config.simulation_name,
                    config.simulation_speed,
                    config.display_size,
                    config.num_houses,
                    config.num_offices,
                    config.building_size,
                    config.num_people_in_house,
                    int(config.show_drawing),
                    int(config.additional_roads),
                    config.infection_rate,
                    config.incubation_time,
                    config.recovery_rate,
                    config.mortality_rate,
                ),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            raise DBError(f"Error saving parameters: {e}")

    def fetch_runs_summary(self) -> list[tuple]:
        """
        Return a summary of previous runs for selection in the UI.
        Columns: run_id, datetime, simulation_name, num_houses, num_offices,
                 infection_rate, incubation_time, recovery_rate, mortality_rate
        """
        try:
            assert self.conn is not None
            cur = self.conn.cursor()
            cur.execute("""
                SELECT run_id, datetime, simulation_name,
                    num_houses, num_offices,
                    infection_rate, incubation_time,
                    recovery_rate, mortality_rate
                FROM simulations
                ORDER BY datetime DESC
            """)
            rows = cur.fetchall()

            summaries = []
            for row in rows:
                summaries.append({
                    "run_id": row[0],
                    "datetime": row[1],
                    "simulation_name": row[2],
                    "num_houses": row[3],
                    "num_offices": row[4],
                    "infection_rate": row[5],
                    "incubation_time": row[6],
                    "recovery_rate": row[7],
                    "mortality_rate": row[8],
                })

            return summaries

        except sqlite3.Error as e:
            raise DBError(f"Error fetching run summaries: {e}")

    def fetch_run(self, run_id: int) -> Optional[dict]:
        """Return a dict of run parameters for a given run_id, or None if not found."""
        try:
            assert self.conn is not None
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM simulations WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if row is None:
                return None

            # Map tuple → dict
            return {
                "simulation_name": row[2],
                "simulation_speed": row[3],
                "display_size": row[4],
                "num_houses": row[5],
                "num_offices": row[6],
                "building_size": row[7],
                "num_people_in_house": row[8],
                "show_drawing": row[9],
                "additional_roads": row[10],
                "infection_rate": row[11],
                "incubation_time": row[12],
                "recovery_rate": row[13],
                "mortality_rate": row[14],
            }

        except sqlite3.Error as e:
            raise DBError(f"Error fetching run {run_id}: {e}")