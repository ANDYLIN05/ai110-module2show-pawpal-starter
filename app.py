import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Constraint

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+. Plan your pet care tasks based on your available time and priorities.
"""
)

# --- Session State Initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60)

if "pet" not in st.session_state:
    st.session_state.pet = None

if "last_schedule" not in st.session_state:
    st.session_state.last_schedule = None

if "last_plan_text" not in st.session_state:
    st.session_state.last_plan_text = None

# --- Owner & Pet Setup ---
st.subheader("Owner & Pet Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes today", min_value=5, max_value=480, value=60)

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
energy_level = st.selectbox("Energy level", ["low", "medium", "high"], index=1)

if st.button("Set Owner & Pet"):
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_minutes = available_minutes
    pet = Pet(name=pet_name, species=species, energy_level=energy_level)
    st.session_state.owner.add_pet(pet)
    st.session_state.pet = pet
    st.success(f"Pet '{pet_name}' added to owner '{owner_name}'!")

st.divider()

# --- Add Tasks ---
st.subheader("Add Tasks")
st.caption("Tasks are added directly to your pet via Pet.add_task().")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    task_time = st.text_input("Scheduled time (HH:MM)", value="09:00")
with col5:
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

if st.button("Add Task"):
    if st.session_state.pet is None:
        st.warning("Set an owner and pet first.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            time=task_time,
            frequency=frequency,
        )
        st.session_state.pet.add_task(task)
        st.success(f"Task '{task_title}' added to {st.session_state.pet.name}!")

# --- Show & Edit/Delete Tasks ---
if st.session_state.pet and st.session_state.pet.tasks:
    st.write(f"Tasks for **{st.session_state.pet.name}**:")
    for i, t in enumerate(st.session_state.pet.tasks):
        col_info, col_edit, col_del = st.columns([4, 1, 1])
        with col_info:
            recur_label = f" | {t.frequency}" if t.frequency != "once" else ""
            st.write(
                f"**{t.title}** — {t.duration_minutes} min | {t.priority} priority"
                f" | {t.time}{recur_label} | done: {t.completed}"
            )
        with col_edit:
            if st.button("Edit", key=f"edit_{i}"):
                st.session_state[f"editing_{i}"] = True
        with col_del:
            if st.button("Delete", key=f"del_{i}"):
                st.session_state.pet.tasks.pop(i)
                st.rerun()

        if st.session_state.get(f"editing_{i}"):
            with st.form(key=f"edit_form_{i}"):
                new_title = st.text_input("Title", value=t.title)
                new_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=t.duration_minutes)
                new_priority = st.selectbox("Priority", ["low", "medium", "high"], index=["low", "medium", "high"].index(t.priority))
                new_time = st.text_input("Scheduled time (HH:MM)", value=t.time)
                new_freq = st.selectbox("Frequency", ["once", "daily", "weekly"], index=["once", "daily", "weekly"].index(t.frequency))
                new_completed = st.checkbox("Mark as completed", value=t.completed)
                save_col, cancel_col = st.columns(2)
                with save_col:
                    submitted = st.form_submit_button("Save")
                with cancel_col:
                    cancelled = st.form_submit_button("Cancel")

            if submitted:
                t.title = new_title
                t.duration_minutes = int(new_duration)
                t.priority = new_priority
                t.time = new_time
                t.frequency = new_freq
                t.completed = new_completed
                del st.session_state[f"editing_{i}"]
                st.rerun()
            elif cancelled:
                del st.session_state[f"editing_{i}"]
                st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Build Schedule ---
st.subheader("Build Schedule")
st.caption("Calls Scheduler.build_master_schedule(), sort_by_time(), and detect_conflicts().")

col_gen, col_reset = st.columns(2)
with col_gen:
    if st.button("Generate Schedule"):
        if not st.session_state.owner.pets:
            st.warning("Set an owner and pet first.")
        else:
            brain = Scheduler(owner=st.session_state.owner)
            schedule = brain.build_master_schedule()
            sorted_schedule = brain.sort_by_time(schedule)
            st.session_state.last_schedule = sorted_schedule
            st.session_state.last_plan_text = brain.explain_plan(sorted_schedule)

with col_reset:
    if st.button("Reset Schedule"):
        st.session_state.last_schedule = None
        st.session_state.last_plan_text = None
        for pet in st.session_state.owner.pets:
            for task in pet.tasks:
                task.completed = False
        st.success("Schedule cleared. Tasks reset to not completed.")

# --- Display Schedule ---
if st.session_state.last_schedule is not None:
    schedule = st.session_state.last_schedule

    # Conflict warnings
    brain = Scheduler(owner=st.session_state.owner)
    conflicts = brain.detect_conflicts(schedule)
    if conflicts:
        st.markdown("#### ⚠️ Scheduling Conflicts")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")

    # Sorted schedule table
    if schedule:
        st.markdown("#### 📋 Today's Schedule (sorted by time)")
        table_data = [
            {
                "Time": pet_task[1].time,
                "Pet": pet_task[0].name,
                "Task": pet_task[1].title,
                "Duration (min)": pet_task[1].duration_minutes,
                "Priority": pet_task[1].priority,
                "Frequency": pet_task[1].frequency,
            }
            for pet_task in schedule
        ]
        st.table(table_data)

        total = sum(t.duration_minutes for _, t in schedule)
        remaining = st.session_state.owner.available_minutes - total
        col_a, col_b = st.columns(2)
        col_a.metric("Total scheduled (min)", total)
        col_b.metric("Remaining (min)", remaining)
    else:
        st.info("No tasks fit within your available time or all tasks are completed.")

    # Full plan explanation (collapsible)
    with st.expander("Show full plan explanation"):
        st.text(st.session_state.last_plan_text)

st.divider()

# --- Filter Tasks ---
st.subheader("Filter Tasks")
st.caption("Uses Scheduler.filter_tasks() to search across all pets.")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    filter_status = st.selectbox("Status", ["All", "Completed", "Incomplete"])
with filter_col2:
    filter_pet = st.text_input("Pet name (leave blank for all)", value="")

if st.button("Apply Filter"):
    if not st.session_state.owner.pets:
        st.warning("No pets added yet.")
    else:
        brain = Scheduler(owner=st.session_state.owner)
        completed_arg = None
        if filter_status == "Completed":
            completed_arg = True
        elif filter_status == "Incomplete":
            completed_arg = False
        pet_name_arg = filter_pet.strip() if filter_pet.strip() else None
        results = brain.filter_tasks(completed=completed_arg, pet_name=pet_name_arg)

        if results:
            st.markdown(f"**{len(results)} task(s) found:**")
            filter_data = [
                {
                    "Pet": p.name,
                    "Task": t.title,
                    "Priority": t.priority,
                    "Duration (min)": t.duration_minutes,
                    "Time": t.time,
                    "Done": t.completed,
                }
                for p, t in results
            ]
            st.table(filter_data)
        else:
            st.info("No tasks match the selected filter.")
