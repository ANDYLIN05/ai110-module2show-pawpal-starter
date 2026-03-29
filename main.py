from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Constraint

def run_test():
    # 1. Setup the Owner
    me = Owner(name="Alex", available_minutes=60)

    # 2. Create Pets
    buddy = Pet(name="Buddy", species="dog", energy_level="high")
    mittens = Pet(name="Mittens", species="cat", energy_level="low")

    me.add_pet(buddy)
    me.add_pet(mittens)

    # 3. Add Tasks — two tasks intentionally share time "07:00" to trigger conflict detection
    buddy.add_task(Task(
        title="Morning Walk", duration_minutes=30, priority="high",
        time="07:00", frequency="daily", due_date=date.today()
    ))
    buddy.add_task(Task(
        title="Brush Fur", duration_minutes=10, priority="low",
        time="09:30", frequency="weekly", due_date=date.today()
    ))
    mittens.add_task(Task(
        title="Laser Pointer Play", duration_minutes=10, priority="medium",
        time="07:00", frequency="daily", due_date=date.today()  # conflicts with Morning Walk
    ))
    mittens.add_task(Task(
        title="Feed Treats", duration_minutes=5, priority="high",
        time="06:45", frequency="once", due_date=date.today()
    ))

    # 4. Initialize the Brain
    brain = Scheduler(owner=me)

    # 5. Build and explain the schedule
    print("--- Generating PawPal+ Master Plan ---")
    schedule = brain.build_master_schedule()
    print(brain.explain_plan(schedule))

    # 6. Detect time conflicts
    print("\n--- Conflict Detection ---")
    conflicts = brain.detect_conflicts(schedule)
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    # 7. Sort by time
    print("\n--- Schedule Sorted by Time ---")
    for pet, task in brain.sort_by_time(schedule):
        print(f"  {task.time}  [{pet.name}] {task.title} ({task.priority}, {task.duration_minutes} min | {task.frequency})")

    # 8. Mark recurring tasks complete
    print("\n--- Completing Recurring Tasks ---")
    for pet, task in schedule:
        next_task = brain.mark_task_complete(pet, task)
        if next_task:
            print(f"  '{task.title}' done. Next {task.frequency} occurrence added -> due {next_task.due_date}")
        else:
            print(f"  '{task.title}' done. (one-time task, no recurrence)")

    # 9. Filter: incomplete tasks (next occurrences)
    print("\n--- Incomplete Tasks After Completion (next occurrences) ---")
    for pet, task in brain.filter_tasks(completed=False):
        print(f"  [{pet.name}] {task.title} -- due: {task.due_date} | frequency: {task.frequency}")

    # 10. Filter by pet name
    print("\n--- All Tasks for Mittens ---")
    for pet, task in brain.filter_tasks(pet_name="Mittens"):
        status = "done" if task.completed else "pending"
        print(f"  {task.title} -- {status} | due: {task.due_date}")

if __name__ == "__main__":
    run_test()
