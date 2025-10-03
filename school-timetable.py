"""
This script builds and solves a small CP-SAT model for assigning subjects to groups and teachers.
It is a minimal translation of the notebook code into a runnable Python script.
"""

from ortools.sat.python import cp_model
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class Subject:
    id: str
    name: str
    course: str
    weekly_hours: int = 5
    max_hours_per_day: int = 1

    def __repr__(self):
        return f"{self.name} ({self.course})"

@dataclass
class Teacher:
    id: int
    name: str
    max_hours_week: int = 20
    subjects: List[Subject] = None

    def __post_init__(self):
        if self.subjects is None:
            self.subjects = []

    def __repr__(self):
        return f"{self.name}, {self.max_hours_week} h/w, {[s.id for s in self.subjects]}"


def build_and_solve(num_days: int = 5, num_hours: int = 5, all_groups: List[str] = [], all_subjects: List[Subject] = [], all_teachers: List[Teacher] = []) -> Tuple[cp_model.CpSolver, Dict]:
    model = cp_model.CpModel()

    # Create decision variables (group-subject-teacher-day-hour)
    assignments = {}
    for group in all_groups:
        course = group.split('-')[0]
        for subject in all_subjects:
            if subject.course == course:
                for teacher in all_teachers:
                    if subject in teacher.subjects:
                        for d in range(num_days):
                            for h in range(num_hours):
                                key = (group, subject.id, teacher.id, d, h)
                                assignments[key] = model.NewBoolVar(f"g:{group} sub:{subject.id} t:{teacher.name} d:{d} h:{h}")

    # Each subject must be taught the specified weekly hours
    for group in all_groups:
        course = group.split('-')[0]
        for subject in all_subjects:
            if subject.course == course:
                model.Add(sum(assignments[key] for key in assignments if key[0] == group and key[1] == subject.id) == subject.weekly_hours)

    # A teacher cannot teach two classes at the same time
    for teacher in all_teachers:
        for d in range(num_days):
            for h in range(num_hours):
                model.AddAtMostOne(assignments[key] for key in assignments if key[2] == teacher.id and key[3] == d and key[4] == h)

    # Teachers cannot exceed their maximum assigned weekly hours.
    for teacher in all_teachers:
        max_hours = teacher.max_hours_week
        teacher_total_hours = sum(assignments[key] for key in assignments if key[2] == teacher.id)
        model.Add(teacher_total_hours <= max_hours)

    # The maximum number of hours per day for each subject and group is limited.
    for group in all_groups:
        course = group.split('-')[0]
        for subject in all_subjects:
            if subject.course == course:
                for teacher in all_teachers:
                    if subject in teacher.subjects:
                        for d in range(num_days):
                            hour_vars = [assignments[key] for key in assignments  if key[0] == group and key[1] == subject.id and key[2] == teacher.id and key[3] == d]
                            model.Add(sum(hour_vars) <= subject.max_hours_per_day)

    # If a subject is taught more than one hour per day in a group, the hours must be consecutive.
    for group in all_groups:
        course = group.split('-')[0]
        for subject in all_subjects:
            if subject.course == course:
                for d in range(num_days):
                    hour_vars = [assignments[key] for key in assignments if key[0] == group and key[1] == subject.id and key[3] == d]
                    if len(hour_vars) >= 2:
                        for h1 in range(len(hour_vars)):
                            for h2 in range(h1 + 1, len(hour_vars)):
                                not_consecutive = model.NewBoolVar(f"not_consecutive_{group}_{subject.id}_{d}_{h1}_{h2}")
                                model.Add(h2 != h1 + 1).OnlyEnforceIf(not_consecutive)
                                model.AddBoolAnd([hour_vars[h1], hour_vars[h2]]).OnlyEnforceIf(not_consecutive)
                                model.Add(not_consecutive == 0)

    # Solve the model
    solver = cp_model.CpSolver()
    solver.Solve(model)
    return solver, assignments


def print_timetables(solver: cp_model.CpSolver, assignments: Dict, num_days: int = 5, num_hours: int = 5):
    def _print_table(title: str, headers: List[str], rows: List[List[str]]):
        # Compute column widths
        cols = len(headers)
        widths = [len(h) for h in headers]
        for r in rows:
            for i in range(cols):
                widths[i] = max(widths[i], len(r[i]))

        sep = " | "
        border = "-+-".join('-' * w for w in widths)

        print(f"\n{title}")
        # Header
        header_line = sep.join(headers[i].ljust(widths[i]) for i in range(cols))
        print(header_line)
        print(border)
        # Rows
        for r in rows:
            print(sep.join(r[i].ljust(widths[i]) for i in range(cols)))

    if solver.StatusName() in ("FEASIBLE", "OPTIMAL"):
        for group in all_groups:
            course = group.split('-')[0]
            title = f"Schedule for {group}"
            headers = ["Hour"] + ["Mon", "Tue", "Wed", "Thu", "Fri"][:num_days]
            rows = []
            for h in range(num_hours):
                row = [f"Hour {h}"]
                for d in range(num_days):
                    cell_content = ""
                    for subject in all_subjects:
                        if subject.course == course:
                            for teacher in all_teachers:
                                if subject in teacher.subjects:
                                    key = (group, subject.id, teacher.id, d, h)
                                    if key in assignments and solver.Value(assignments[key]) == 1:
                                        cell_content = f"{subject.name} ({teacher.name})"
                    row.append(cell_content if cell_content else "-")
                rows.append(row)

            _print_table(title, headers, rows)
    else:
        print("No feasible solution found.")


if __name__ == "__main__":
    
    all_groups = ["1-A", "1-B"]
    math1 = Subject(id="math1", name="Maths", course="1", weekly_hours=10, max_hours_per_day=2)
    all_subjects = [math1]

    John = Teacher(id=1, name="John", max_hours_week=25, subjects=[math1])
    all_teachers = [John]

    solver, assignments = build_and_solve(num_days=5, num_hours=5, all_groups=all_groups, all_subjects=all_subjects, all_teachers=all_teachers)
    
    print_timetables(solver, assignments)
