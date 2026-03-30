# 🐾 PawPal+

A Streamlit app that helps a pet owner plan daily care tasks using priority-based scheduling, conflict detection, and recurring task logic.

---

## 📸 Demo

**1 - Owner & Pet Setup**

![Setup](screenshots/PawPal_SetUp.PNG)

**2 - Task List**

![Tasks](screenshots/PawPal_AddTask.PNG)

**3 - Generated Schedule & Conflict Detection**

![Schedule](screenshots/PawPal_BuildSchedule.PNG)

**4 - Filter Tasks**

![Filter](screenshots/PawPal_FilterTask.PNG)

---

## Features

- **Owner & Pet setup** — Enter the owner's name, available minutes for the day, and add one or more pets with a species and energy level.
- **Task management** — Add, edit, and delete tasks with a title, duration, priority (high / medium / low), scheduled time (HH:MM), and frequency (once / daily / weekly).
- **Priority-based scheduling** — `Scheduler.build_master_schedule()` sorts tasks by priority and greedily fits them within the owner's time budget.
- **Chronological sorting** — `Scheduler.sort_by_time()` reorders the schedule from earliest to latest so the display always reads in time order.
- **Conflict detection** — `Scheduler.detect_conflicts()` scans the schedule for tasks sharing the same time slot and surfaces each conflict as a `st.warning` banner.
- **Recurring tasks** — Daily and weekly tasks automatically generate the next occurrence (with the correct future date) when marked complete via `Scheduler.mark_task_complete()`.
- **Task filtering** — `Scheduler.filter_tasks()` lets you view tasks by completion status and/or pet name across all pets.
- **Plan explanation** — `Scheduler.explain_plan()` produces a human-readable summary showing what was scheduled, what was skipped, and how much time remains.

---

## Project Structure

```
pawpal_system.py   # Core logic — Task, Pet, Owner, Constraint, Scheduler
app.py             # Streamlit UI
tests/
  test_pawpal.py   # Automated test suite (pytest)
uml_final.md       # Final Mermaid.js class diagram
reflection.md      # Project reflection
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

## Run Tests

```bash
python -m pytest
```

Confidence Level: ⭐⭐⭐⭐⭐

---

## UML Diagram

The Mermaid source is in [`pawpal_system.py`](pawpal_system.py) at the top of the file.

![PawPal+ UML Diagram](/screenshots/uml_final.PNG)
