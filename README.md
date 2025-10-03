# School Timetable Generator

A small constraint-programming example that builds a weekly school timetable using OR-Tools CP-SAT. The project is provided as a Jupyter notebook, `school-timetable.ipynb`, and a standalone script extracted from it.

## Files

- `school-timetable.ipynb` — the Jupyter notebook with the full model and example data.
- `school_timetable.py` — standalone Python script (extracted from the notebook).

## Package manager (uv)
To install dependencies and run the project using `uv` (recommended if you use `uv.lock`):

```sh
# Install uv (see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restore/install dependencies from uv.lock
uv sync

# Run the script via uv (uses the locked environment)
uv run school_timetable.py
```

If you don't use `uv`, see the Quickstart (pip) section below.

## Quickstart (pip)
If you prefer not to use `uv`, create and activate a virtual environment and install the minimal runtime packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install jupyter ortools
```

Run the notebook with `jupyter notebook school-timetable.ipynb`, or run the script directly with `python3 school_timetable.py`.

## Example configuration (inside the notebook/script)

Key parameters you can edit directly in the notebook or script:

- `num_days`, `num_hours` — timetable dimensions (days per week, hours per day).
- `all_groups` — list of group identifiers. e.g. `["1-A", "1-B"]`
- `all_subjects` — list of `Subject(...)` instances with `weekly_hours` and `max_hours_per_day`.
- `all_teachers` — list of `Teacher(...)` instances with `max_hours_week` and `subjects` they can teach.

## Notes & limitations

- This repository is a demonstration and prioritises clarity over performance or production readiness.
- The model is intentionally simple; real school timetabling often requires more features (rooms, part-time availability, shared subjects, soft preferences, etc.).
- If you see a runtime error such as `ModuleNotFoundError: No module named 'ortools'`, install OR-Tools in your environment (see Quickstart).

## License

This repository contains example code. No license file is included; add one if you plan to reuse or redistribute the code.
