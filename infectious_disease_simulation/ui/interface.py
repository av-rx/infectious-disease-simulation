"""Tkinter front-end for collecting simulation parameters.

This module is intentionally backend-free: it does not import Config, DBHandler, or any
simulation code. Validation and DB access are passed in as callables so the UI can be
tested or swapped without touching the rest of the codebase.
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable


class Interface:
    """Parameter-entry window. Call `get_params()` to run the event loop and retrieve the result."""

    def __init__(self,
                 fetch_runs_summary: Callable[[], list[dict]],
                 fetch_run: Callable[[int], dict | None],
                 validate: Callable[[dict], Any]) -> None:
        """
        Args:
            fetch_runs_summary: Returns previous-run rows for the "Load Previous Run" window.
            fetch_run: Returns a single previous-run's params dict by run_id, or None if missing.
            validate: Called with the submitted params dict; should raise on invalid values.
                      The raised exception's str() is shown in a "Configuration Error" dialog.
        """
        self.__fetch_runs_summary = fetch_runs_summary
        self.__fetch_run = fetch_run
        self.__validate = validate

        self.__root: tk.Tk = tk.Tk()
        self.__root.title("Simulation Parameters")

        self.__style: ttk.Style = ttk.Style()
        self.__style.configure("TLabel", padding=6)

        self.__params: dict[str, Any] = {}        # widget refs while window is open
        self.__submitted: dict | None = None      # final dict, populated on successful submit

        self.__create_widgets()
        self.__root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__load_window: tk.Toplevel | None = None

    def get_params(self) -> dict | None:
        """Run the GUI event loop and return the submitted params dict (or None if cancelled)."""
        self.__root.mainloop()
        return self.__submitted

    def __create_widgets(self) -> None:
        """Build every input frame, the run/load buttons, and the speed slider."""
        # Simulation Name and Speed
        simulation_frame: ttk.LabelFrame = ttk.LabelFrame(self.__root, text="Simulation")
        simulation_frame.grid(row=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(simulation_frame, text="Simulation Name:").grid(row=0, column=0, sticky="w")
        self.__params["simulation_name"] = ttk.Entry(simulation_frame)
        self.__params["simulation_name"].insert(0, "Simulation")
        self.__params["simulation_name"].grid(row=0, column=1, sticky="w")

        ttk.Label(simulation_frame, text="Simulation Speed:").grid(row=1, column=0, sticky="w")
        self.__simulation_speed: tk.DoubleVar = tk.DoubleVar(value=2)
        self.__simulation_speed_scale: ttk.Scale = ttk.Scale(
            simulation_frame, from_=0.5, to=5.0, variable=self.__simulation_speed, orient='horizontal',
            command=self.__update_speed_label, length=150
        )
        self.__simulation_speed_scale.grid(row=1, column=1, sticky="ew")
        self.__simulation_speed_label: ttk.Label = ttk.Label(simulation_frame, text="2x")
        self.__simulation_speed_label.grid(row=1, column=2, sticky="w")

        self.__simulation_speed_values: list[float] = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        self.__simulation_speed_scale.set(self.__simulation_speed_values[3])

        # Display Parameters
        display_frame: ttk.LabelFrame = ttk.LabelFrame(self.__root, text="Display")
        display_frame.grid(row=1, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(display_frame, text="Display Size (pixels):").grid(row=0, column=0, sticky="w")
        self.__params["display_size"] = ttk.Entry(display_frame)
        self.__params["display_size"].insert(0, "800")
        self.__params["display_size"].grid(row=0, column=1)

        # Map Parameters
        map_frame: ttk.LabelFrame = ttk.LabelFrame(self.__root, text="Map")
        map_frame.grid(row=2, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(map_frame, text="Number of Houses:").grid(row=0, column=0, sticky="w")
        self.__params["num_houses"] = ttk.Entry(map_frame)
        self.__params["num_houses"].insert(0, "75")
        self.__params["num_houses"].grid(row=0, column=1)

        ttk.Label(map_frame, text="Number of Offices:").grid(row=1, column=0, sticky="w")
        self.__params["num_offices"] = ttk.Entry(map_frame)
        self.__params["num_offices"].insert(0, "25")
        self.__params["num_offices"].grid(row=1, column=1)

        ttk.Label(map_frame, text="Building Size (pixels):").grid(row=2, column=0, sticky="w")
        self.__params["building_size"] = ttk.Entry(map_frame)
        self.__params["building_size"].insert(0, "50")
        self.__params["building_size"].grid(row=2, column=1)

        # Population Parameters
        population_frame: ttk.LabelFrame = ttk.LabelFrame(self.__root, text="Population")
        population_frame.grid(row=3, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(population_frame, text="Number of People per House:").grid(row=0, column=0, sticky="w")
        self.__params["num_people_in_house"] = ttk.Entry(population_frame)
        self.__params["num_people_in_house"].insert(0, "4")
        self.__params["num_people_in_house"].grid(row=0, column=1)

        # Map Drawing Parameters
        map_drawing_frame: ttk.Label = ttk.LabelFrame(self.__root, text="Map Drawing")
        map_drawing_frame.grid(row=4, columnspan=2, padx=10, pady=10, sticky="ew")

        self.__show_drawing: tk.BooleanVar = tk.BooleanVar(value=True)
        ttk.Checkbutton(map_drawing_frame, text="Show Map Drawing Process",
                        variable=self.__show_drawing).grid(row=0, columnspan=2, sticky="w")

        self.__additional_roads: tk.BooleanVar = tk.BooleanVar(value=True)
        ttk.Checkbutton(map_drawing_frame, text="Draw Additional Roads",
                        variable=self.__additional_roads).grid(row=1, columnspan=2, sticky="w")

        # Disease Parameters
        disease_frame: ttk.LabelFrame = ttk.LabelFrame(self.__root, text="Disease")
        disease_frame.grid(row=5, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(disease_frame, text="Infection Rate:").grid(row=0, column=0, sticky="w")
        self.__params["infection_rate"] = ttk.Entry(disease_frame)
        self.__params["infection_rate"].insert(0, "0.7")
        self.__params["infection_rate"].grid(row=0, column=1)
        ttk.Label(disease_frame,
                  text="Probability of a contact getting infected. Decimal between 0 and 1.").grid(
                      row=1, column=0, columnspan=2, sticky="w")

        ttk.Label(disease_frame, text="Incubation Time:").grid(row=2, column=0, sticky="w")
        self.__params["incubation_time"] = ttk.Entry(disease_frame)
        self.__params["incubation_time"].insert(0, "2.0")
        self.__params["incubation_time"].grid(row=2, column=1)
        ttk.Label(disease_frame,
                  text="Period in days after contracting disease before becoming infectious.").grid(
                      row=3, column=0, columnspan=2, sticky="w")

        ttk.Label(disease_frame, text="Recovery Rate:").grid(row=4, column=0, sticky="w")
        self.__params["recovery_rate"] = ttk.Entry(disease_frame)
        self.__params["recovery_rate"].insert(0, "0.6")
        self.__params["recovery_rate"].grid(row=4, column=1)
        ttk.Label(disease_frame,
                  text="Probability of an infected person recovering. Decimal between 0 and 1.").grid(
                      row=5, column=0, columnspan=2, sticky="w")

        ttk.Label(disease_frame, text="Mortality Rate:").grid(row=6, column=0, sticky="w")
        self.__params["mortality_rate"] = ttk.Entry(disease_frame)
        self.__params["mortality_rate"].insert(0, "0.1")
        self.__params["mortality_rate"].grid(row=6, column=1)
        ttk.Label(disease_frame,
                  text="Probability of an infected person dying. Decimal between 0 and 1.").grid(
                      row=7, column=0, columnspan=2, sticky="w")

        # Run and Load Buttons
        ttk.Button(self.__root, text="Run Simulation", command=self.__submit).grid(row=6, column=0, pady=10)
        ttk.Button(self.__root, text="Load Previous Run",
                   command=self.__load_previous_run).grid(row=6, column=1, pady=10)

    def __update_speed_label(self, value: float) -> None:
        """Snap the slider to the nearest predefined speed value and update the label."""
        closest: float = min(self.__simulation_speed_values, key=lambda s: abs(s - float(value)))
        self.__simulation_speed.set(closest)
        self.__simulation_speed_label.config(text=f"{closest}x")

    def __submit(self) -> None:
        """Read fields, run input-format checks, run validate(), show warnings, then close on success."""
        try:
            raw = self.__collect_params()
        except TypeError as e:
            messagebox.showerror("Format Error", f"Invalid input: {e}")
            return
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return

        # Semantic validation lives in the injected validator (Config.from_dict in production)
        try:
            self.__validate(raw)
        except Exception as e:
            messagebox.showerror("Configuration Error", str(e))
            return

        # User-acknowledgable warnings — these are UX, not validation, so they stay in the UI
        if not self.__confirm_warnings(raw):
            return

        self.__submitted = raw
        self.__root.quit()
        self.__root.destroy()

    def __collect_params(self) -> dict[str, Any]:
        """Read every entry/var into a raw dict, casting strings to the expected types."""
        return {
            "simulation_name": self.__cast(str, self.__params["simulation_name"].get()),
            "simulation_speed": self.__cast(float, self.__simulation_speed.get()),
            "display_size": self.__cast(int, self.__params["display_size"].get()),
            "num_houses": self.__cast(int, self.__params["num_houses"].get()),
            "num_offices": self.__cast(int, self.__params["num_offices"].get()),
            "building_size": self.__cast(int, self.__params["building_size"].get()),
            "num_people_in_house": self.__cast(int, self.__params["num_people_in_house"].get()),
            "show_drawing": self.__show_drawing.get(),
            "additional_roads": self.__additional_roads.get(),
            "infection_rate": self.__cast(float, self.__params["infection_rate"].get()),
            "incubation_time": self.__cast(float, self.__params["incubation_time"].get()),
            "recovery_rate": self.__cast(float, self.__params["recovery_rate"].get()),
            "mortality_rate": self.__cast(float, self.__params["mortality_rate"].get()),
        }

    def __confirm_warnings(self, raw: dict[str, Any]) -> bool:
        """Show non-blocking warnings for unusual but valid configs. Returns False if the user cancels."""
        nh = raw["num_houses"]
        no = raw["num_offices"]
        ppl = raw["num_people_in_house"]
        bs = raw["building_size"]
        rec = raw["recovery_rate"]
        mort = raw["mortality_rate"]

        if ppl * nh >= 1000:
            if not messagebox.askokcancel(
                "Warning",
                "The population size is large and initialisation may take long.\n"
                "The simulation may not run smoothly on all systems.\n"
                "Consider reducing the total number of people, or simulation speed if performance is an issue.\n"
                "Proceed?",
                icon='warning', default='cancel'):
                return False

        if nh + no >= 500:
            if not messagebox.askokcancel(
                "Warning",
                "There are a large number of buildings and the road network may take time to generate.\n"
                "Consider reducing the total number of buildings if this is an issue.\n"
                "Proceed?",
                icon='warning', default='cancel'):
                return False

        if rec == 0 and mort == 0:
            if not messagebox.askokcancel(
                "Warning",
                "Both the recovery rate and mortality rate are 0, so the simulation will not end.\n"
                "Proceed?",
                icon='warning', default='cancel'):
                return False

        # Visibility check: people too small to render distinguishably
        # min radius needs to be >= 1 in every building (home and office crowds)
        too_small = (
            bs // 10 < 1
            or bs // (2 * (math.ceil(math.sqrt(ppl)) + 1)) < 1
            or bs // (2 * (math.ceil(math.sqrt((ppl * nh) // no)) + 1)) < 1
        )
        if too_small:
            if not messagebox.askokcancel(
                "Warning",
                "Population size too large and/or building size too small for people to be seen.\n"
                "Proceed?",
                icon='warning', default='cancel'):
                return False

        return True

    def __on_closing(self) -> None:
        """Window-close handler: clear submission and exit the mainloop."""
        self.__submitted = None
        self.__root.quit()

    @staticmethod
    def __cast(variable_type: type, value: Any) -> Any:
        """Cast `value` to `variable_type`. Raises TypeError on blank/NaN/uncastable strings."""
        # Generalised input prompt suffix per type
        type_suffix = {int: "n integer", float: " decimal", str: " sequence of characters"}

        # tkinter Entry widgets always return strings; DoubleVar etc. return numerics. Only string
        # values need the format checks below.
        if isinstance(value, str):
            if value == '':
                raise TypeError(f"<blank field>. Please enter a{type_suffix[variable_type]}.")
            if value in ('inf', 'Inf', 'infinity', 'Infinity', 'nan', 'Nan', 'NaN'):
                raise TypeError(f"'{value}'. Please enter a{type_suffix[variable_type]}.")

        try:
            return variable_type(value)
        except Exception:
            raise TypeError(f"'{value}'. Please enter a{type_suffix[variable_type]}.")

    def __load_previous_run(self) -> None:
        """Open the previous-runs selection window."""
        if self.__load_window is not None and self.__load_window.winfo_exists():
            self.__load_window.lift()
            return

        try:
            rows = self.__fetch_runs_summary()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return

        if not rows:
            messagebox.showinfo("Load Previous Run", "No previous runs found.")
            return

        self.__load_window = tk.Toplevel(self.__root)
        self.__load_window.title("Select Previous Run")
        self.__load_window.protocol("WM_DELETE_WINDOW", self.__close_load_window)

        frame = ttk.Frame(self.__load_window)
        frame.grid(row=0, column=0, padx=10, pady=10)

        tree = ttk.Treeview(
            frame,
            columns=("run_id", "datetime", "simulation_name",
                     "num_houses", "num_offices",
                     "infection_rate", "incubation_time",
                     "recovery_rate", "mortality_rate"),
            show='headings'
        )
        for col in tree["columns"]:
            tree.heading(col, text=col.replace("_", " ").title(), anchor="center")
            tree.column(col, width=150, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        for summary in rows:
            tree.insert("", "end", values=(
                summary["run_id"], summary["datetime"], summary["simulation_name"],
                summary["num_houses"], summary["num_offices"],
                summary["infection_rate"], summary["incubation_time"],
                summary["recovery_rate"], summary["mortality_rate"],
            ))

        ttk.Button(self.__load_window, text="Load",
                   command=lambda: self.__load_selected_run(tree)).grid(row=1, column=0, padx=10, pady=10)

    def __load_selected_run(self, tree: ttk.Treeview) -> None:
        """Pull the highlighted row's run_id and populate the form from it."""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Selection Error", "No run selected. Please select a run to load.")
            return

        run_id = tree.item(selected_item)["values"][0]
        try:
            loaded = self.__fetch_run(run_id)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return

        if not loaded:
            messagebox.showerror("Load Error", "Selected run not found.")
            return

        # Fill entry widgets
        for key, value in loaded.items():
            if key in self.__params:
                widget = self.__params[key]
                widget.delete(0, tk.END)
                widget.insert(0, value)

        # Fill non-entry widgets
        self.__simulation_speed.set(loaded["simulation_speed"])
        self.__update_speed_label(loaded["simulation_speed"])
        self.__show_drawing.set(loaded["show_drawing"])
        self.__additional_roads.set(loaded["additional_roads"])

        self.__close_load_window()

    def __close_load_window(self) -> None:
        if self.__load_window is not None:
            self.__load_window.destroy()
            self.__load_window = None
