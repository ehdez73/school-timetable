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

    # A group cannot have more than one subject assigned in the same hour.
    for group in all_groups:
        for d in range(num_days):
            for h in range(num_hours):
                model.Add(sum(assignments[k] for k in assignments if k[0]==group and k[3]==d and k[4]==h) <= 1)
            
    # If a subject is taught more than one hour per day in a group, the hours must be consecutive.
    for group in all_groups:
        course = group.split('-')[0]
        for subject in all_subjects:
            if subject.course == course:
                for d in range(num_days):
                    # 1) create aggregated variables y_h
                    y_vars = []
                    for h in range(num_hours):
                        y = model.NewBoolVar(f"y_{group}_{subject.id}_d{d}_h{h}")  # y[group,subject,day,h]
                        # Link y with the assignment variables (sum over teachers)
                        assign_vars = [
                            assignments[key]
                            for key in assignments
                            if key[0] == group and key[1] == subject.id and key[3] == d and key[4] == h
                        ]
                        if assign_vars:
                            # Equality: y == sum(assign_vars). (Assumes no two teachers simultaneously for the same group-subject-slot.)
                            model.Add(sum(assign_vars) == y)
                        else:
                            # if there are no possible teachers for that slot, force y == 0
                            model.Add(y == 0)
                        y_vars.append(y)

                    # 2) define starts: start_h = 1 if y_h == 1 and y_{h-1} == 0
                    starts = []
                    for h in range(num_hours):
                        s = model.NewBoolVar(f"start_{group}_{subject.id}_d{d}_h{h}")
                        starts.append(s)
                        if h == 0:
                            # start at h=0 <=> y_0
                            model.Add(s == y_vars[0])
                        else:
                            # linearization of s == y_h & (not y_{h-1}):
                            #  s >= y_h - y_{h-1}
                            #  s <= y_h
                            #  s <= 1 - y_{h-1}
                            model.Add(s >= y_vars[h] - y_vars[h-1])
                            model.Add(s <= y_vars[h])
                            model.Add(s <= 1 - y_vars[h-1])

                    # 3) at most one block start per day -> ensures a single contiguous block (or none)
                    model.Add(sum(starts) <= 1)

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

    # groups
    all_groups = ["1-A", "1-B"]
    
    # subjects
    math1 = Subject(id="math1", name="Maths", course="1", weekly_hours=10, max_hours_per_day=2)
    eng1 = Subject(id="eng1", name="English", course="1", weekly_hours=10, max_hours_per_day=2)
    all_subjects = [math1,eng1]

    # teachers
    John = Teacher(id=1, name="John", max_hours_week=20, subjects=[math1])
    Jane = Teacher(id=2, name="Jane", max_hours_week=20, subjects=[eng1])
    all_teachers = [John, Jane]

    solver, assignments = build_and_solve(num_days=5, num_hours=5, all_groups=all_groups, all_subjects=all_subjects, all_teachers=all_teachers)
    
    print_timetables(solver, assignments)
