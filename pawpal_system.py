"""
PawPal+ Logic Layer
-------------------
Mermaid.js Class Diagram (paste into https://mermaid.live to view):

```mermaid
classDiagram
    class Owner {
        +str name
        +int available_minutes
        +list~Pet~ pets
        +add_pet(pet)
        +all_pet_tasks() list~tuple~
    }

    class Pet {
        +str name
        +str species
        +str energy_level
        +list~Task~ tasks
        +add_task(task)
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
        +bool completed
        +mark_done()
    }

    class Constraint {
        +str label
        +str applies_to_species
        +str required_priority
        +check(task, pet) bool
    }

    class Scheduler {
        +Owner owner
        +list~Constraint~ constraints
        +add_constraint(constraint)
        +build_master_schedule() list
        +explain_plan(schedule) str
    }

    Owner "1" --> "1..*" Pet : has
    Pet "1" o-- "*" Task : stores
    Scheduler --> Owner : retrieves all tasks from
    Scheduler "1" o-- "*" Constraint : applies
```
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    completed: bool = False
    time: str = "00:00"          # Scheduled time in "HH:MM" format
    frequency: str = "once"      # Recurrence: "once", "daily", or "weekly"
    due_date: date | None = None  # Date this occurrence is due

    def mark_done(self):
        self.completed = True

    def next_occurrence(self) -> "Task":
        """Return a new Task for the next recurrence based on frequency."""
        base = self.due_date if self.due_date else date.today()
        if self.frequency == "daily":
            next_due = base + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = base + timedelta(weeks=1)
        else:
            raise ValueError(f"Task '{self.title}' has frequency='once'; no next occurrence.")
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            time=self.time,
            frequency=self.frequency,
            due_date=next_due,
        )


@dataclass
class Pet:
    name: str
    species: str
    energy_level: str = "medium"
    tasks: list[Task] = field(default_factory=list)  # Required: Pet stores its tasks

    def add_task(self, task: Task):
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    available_minutes: int = 60
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self.pets.append(pet)

    @property
    def all_pet_tasks(self) -> list[tuple[Pet, Task]]:
        """Required: Provides access to all tasks across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Constraint:
    """A rule that gates whether a task should be included in the schedule."""
    label: str
    applies_to_species: str | None = None  # None means applies to all species
    required_priority: str | None = None   # None means no priority filter

    def check(self, task: Task, pet: Pet) -> bool:
        """Return True if the task passes this constraint."""
        if self.applies_to_species and pet.species != self.applies_to_species:
            return True  # constraint doesn't apply to this species, pass through
        if self.required_priority:
            return PRIORITY_ORDER[task.priority] <= PRIORITY_ORDER[self.required_priority]
        return True


class Scheduler:  # The "Brain"
    def __init__(self, owner: Owner):
        self.owner = owner
        self.constraints: list[Constraint] = []

    def add_constraint(self, constraint: Constraint):
        self.constraints.append(constraint)

    def _passes_constraints(self, task: Task, pet: Pet) -> bool:
        return all(c.check(task, pet) for c in self.constraints)

    def build_master_schedule(self) -> list[tuple[Pet, Task]]:
        """Manages tasks ACROSS pets based on owner's time."""
        # Filter and sort in one pass: incomplete tasks that pass constraints, highest priority first
        eligible = sorted(
            (
                (pet, task) for pet, task in self.owner.all_pet_tasks
                if not task.completed and self._passes_constraints(task, pet)
            ),
            key=lambda item: PRIORITY_ORDER[item[1].priority],
        )

        # Budget time: greedily fit tasks within available minutes
        schedule = []
        time_left = self.owner.available_minutes
        for pet, task in eligible:
            if task.duration_minutes <= time_left:
                schedule.append((pet, task))
                time_left -= task.duration_minutes

        return schedule

    def mark_task_complete(self, pet: Pet, task: Task) -> Task | None:
        """Mark a task done. If it recurs, add the next occurrence to the pet and return it."""
        task.mark_done()
        if task.frequency in ("daily", "weekly"):
            next_task = task.next_occurrence()
            pet.add_task(next_task)
            return next_task
        return None

    def detect_conflicts(self, schedule: list[tuple[Pet, Task]]) -> list[str]:
        """Return warning strings for any tasks sharing the same scheduled time."""
        by_time: dict[str, list] = defaultdict(list)
        for pet, task in schedule:
            by_time[task.time].append((pet, task))

        return [
            f"WARNING: Time conflict at {slot} -> "
            + ", ".join(f"[{p.name}] {t.title}" for p, t in items)
            for slot, items in by_time.items()
            if len(items) > 1
        ]

    def sort_by_time(self, schedule: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return schedule sorted by each task's time attribute (HH:MM string)."""
        return sorted(schedule, key=lambda item: item[1].time)

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs filtered by completion status and/or pet name."""
        results = self.owner.all_pet_tasks
        if completed is not None:
            results = [(pet, task) for pet, task in results if task.completed == completed]
        if pet_name is not None:
            results = [(pet, task) for pet, task in results if pet.name == pet_name]
        return results

    def explain_plan(self, schedule: list[tuple[Pet, Task]]) -> str:
        if not schedule:
            return (
                f"No tasks could be scheduled for any pet "
                f"within {self.owner.available_minutes} minutes."
            )

        total = sum(task.duration_minutes for _, task in schedule)
        lines = [
            f"Master Schedule for {self.owner.name} "
            f"— {self.owner.available_minutes} min available.\n"
        ]
        for i, (pet, task) in enumerate(schedule, 1):
            lines.append(
                f"  {i}. [{pet.name}] {task.title} "
                f"[{task.priority} priority, {task.duration_minutes} min]"
            )
        lines.append(f"\nTotal time: {total} min | Remaining: {self.owner.available_minutes - total} min")

        # Show skipped tasks
        scheduled_tasks = [task for _, task in schedule]
        skipped = [
            f"{pet.name}: {task.title}"
            for pet, task in self.owner.all_pet_tasks
            if task not in scheduled_tasks and not task.completed
        ]
        if skipped:
            lines.append(f"Skipped (time or constraint): {', '.join(skipped)}")

        return "\n".join(lines)