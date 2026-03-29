import pytest
from datetime import date, timedelta
from pawpal_system import Pet, Task, Owner, Scheduler

# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------

def test_task_completion():
    """Verify that calling mark_done() actually changes the task's status."""
    task = Task(title="Afternoon Nap", duration_minutes=20)
    assert task.completed is False
    task.mark_done()
    assert task.completed is True


def test_task_addition():
    """Verify that adding a task to a Pet increases that pet's task count."""
    my_pet = Pet(name="Luna", species="dog")
    new_task = Task(title="Fetch", duration_minutes=15)
    initial_count = len(my_pet.tasks)
    my_pet.add_task(new_task)
    assert len(my_pet.tasks) == initial_count + 1
    assert my_pet.tasks[0].title == "Fetch"


# ---------------------------------------------------------------------------
# Helper: build a minimal Scheduler with one pet
# ---------------------------------------------------------------------------

def _make_scheduler(pet: Pet, available_minutes: int = 120) -> Scheduler:
    owner = Owner(name="Alex", available_minutes=available_minutes)
    owner.add_pet(pet)
    return Scheduler(owner)


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks should come back sorted earliest-to-latest by HH:MM."""
    pet = Pet(name="Mochi", species="cat")
    pet.add_task(Task(title="Dinner",    duration_minutes=10, time="18:00"))
    pet.add_task(Task(title="Morning Run", duration_minutes=20, time="07:30"))
    pet.add_task(Task(title="Midday Walk", duration_minutes=15, time="12:00"))

    scheduler = _make_scheduler(pet)
    raw_schedule = scheduler.owner.all_pet_tasks          # unsorted
    sorted_schedule = scheduler.sort_by_time(raw_schedule)

    times = [task.time for _, task in sorted_schedule]
    assert times == sorted(times), f"Expected sorted times, got: {times}"


def test_sort_by_time_single_task():
    """A single-task schedule is trivially sorted — no crash, same item returned."""
    pet = Pet(name="Rex", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=30, time="09:00"))
    scheduler = _make_scheduler(pet)
    result = scheduler.sort_by_time(scheduler.owner.all_pet_tasks)
    assert len(result) == 1
    assert result[0][1].title == "Walk"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_occurrence_on_complete():
    """Marking a daily task done should add a new task due the following day."""
    today = date.today()
    pet = Pet(name="Biscuit", species="dog")
    daily_walk = Task(
        title="Morning Walk",
        duration_minutes=30,
        frequency="daily",
        due_date=today,
    )
    pet.add_task(daily_walk)
    scheduler = _make_scheduler(pet)

    next_task = scheduler.mark_task_complete(pet, daily_walk)

    assert daily_walk.completed is True
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.title == "Morning Walk"
    assert next_task.completed is False
    # The new occurrence should now be in the pet's task list
    assert next_task in pet.tasks


def test_weekly_task_creates_next_occurrence_one_week_later():
    """Marking a weekly task done should schedule the next occurrence 7 days out."""
    today = date.today()
    pet = Pet(name="Whiskers", species="cat")
    bath = Task(title="Bath", duration_minutes=45, frequency="weekly", due_date=today)
    pet.add_task(bath)
    scheduler = _make_scheduler(pet)

    next_task = scheduler.mark_task_complete(pet, bath)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_once_task_returns_none_on_complete():
    """A 'once' task should return None (no next occurrence) when marked done."""
    pet = Pet(name="Goldie", species="fish")
    vet_visit = Task(title="Vet Visit", duration_minutes=60, frequency="once")
    pet.add_task(vet_visit)
    scheduler = _make_scheduler(pet)

    result = scheduler.mark_task_complete(pet, vet_visit)

    assert vet_visit.completed is True
    assert result is None


def test_once_task_next_occurrence_raises():
    """Calling next_occurrence() on a 'once' task should raise ValueError."""
    task = Task(title="One-Time Grooming", duration_minutes=40, frequency="once")
    with pytest.raises(ValueError, match="frequency='once'"):
        task.next_occurrence()


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_same_time():
    """Two tasks scheduled at the same time should produce a conflict warning."""
    pet = Pet(name="Duo", species="dog")
    pet.add_task(Task(title="Walk",  duration_minutes=20, time="09:00"))
    pet.add_task(Task(title="Bath",  duration_minutes=30, time="09:00"))
    scheduler = _make_scheduler(pet)

    schedule = scheduler.owner.all_pet_tasks
    conflicts = scheduler.detect_conflicts(schedule)

    assert len(conflicts) == 1
    assert "09:00" in conflicts[0]
    assert "Walk" in conflicts[0]
    assert "Bath" in conflicts[0]


def test_detect_conflicts_none_when_times_differ():
    """Tasks at different times should produce zero conflict warnings."""
    pet = Pet(name="Solo", species="dog")
    pet.add_task(Task(title="Walk",  duration_minutes=20, time="08:00"))
    pet.add_task(Task(title="Lunch", duration_minutes=15, time="12:30"))
    scheduler = _make_scheduler(pet)

    conflicts = scheduler.detect_conflicts(scheduler.owner.all_pet_tasks)

    assert conflicts == []


def test_detect_conflicts_empty_schedule():
    """An empty schedule should never raise and should return no conflicts."""
    pet = Pet(name="Empty", species="cat")   # no tasks
    scheduler = _make_scheduler(pet)
    conflicts = scheduler.detect_conflicts([])
    assert conflicts == []


# ---------------------------------------------------------------------------
# Edge cases: pet with no tasks
# ---------------------------------------------------------------------------

def test_build_schedule_pet_with_no_tasks():
    """A pet with no tasks should produce an empty master schedule without error."""
    pet = Pet(name="Lazy", species="cat")
    scheduler = _make_scheduler(pet)
    schedule = scheduler.build_master_schedule()
    assert schedule == []


def test_explain_plan_empty_schedule_message():
    """explain_plan on an empty schedule should return the 'no tasks' message."""
    pet = Pet(name="Lazy", species="cat")
    scheduler = _make_scheduler(pet, available_minutes=30)
    message = scheduler.explain_plan([])
    assert "No tasks could be scheduled" in message


# ---------------------------------------------------------------------------
# Time budget enforcement
# ---------------------------------------------------------------------------

def test_build_schedule_respects_time_budget():
    """Tasks that exceed the owner's available minutes should be excluded."""
    pet = Pet(name="Buddy", species="dog")
    pet.add_task(Task(title="Short Walk", duration_minutes=10, priority="high"))
    pet.add_task(Task(title="Long Swim",  duration_minutes=90, priority="high"))

    # Only 30 minutes available — Long Swim (90 min) must not appear
    scheduler = _make_scheduler(pet, available_minutes=30)
    schedule = scheduler.build_master_schedule()

    titles = [task.title for _, task in schedule]
    assert "Short Walk" in titles
    assert "Long Swim" not in titles
