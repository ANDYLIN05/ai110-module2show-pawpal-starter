import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Constraint

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

Use this app to plan pet care tasks based on your available time and priorities.
"""
)

# --- Session State Initialization ---
# Guard each key so data persists across reruns without being overwritten.
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
    # Update owner settings in-place so existing pets are preserved
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

if st.button("Add Task"):
    if st.session_state.pet is None:
        st.warning("Set an owner and pet first.")
    else:
        task = Task(title=task_title, duration_minutes=int(duration), priority=priority)
        st.session_state.pet.add_task(task)
        st.success(f"Task '{task_title}' added to {st.session_state.pet.name}!")

# --- Show & Edit/Delete Tasks ---
if st.session_state.pet and st.session_state.pet.tasks:
    st.write(f"Tasks for **{st.session_state.pet.name}**:")
    for i, t in enumerate(st.session_state.pet.tasks):
        col_info, col_edit, col_del = st.columns([4, 1, 1])
        with col_info:
            st.write(f"**{t.title}** — {t.duration_minutes} min | {t.priority} priority | done: {t.completed}")
        with col_edit:
            if st.button("Edit", key=f"edit_{i}"):
                st.session_state[f"editing_{i}"] = True
        with col_del:
            if st.button("Delete", key=f"del_{i}"):
                st.session_state.pet.tasks.pop(i)
                st.rerun()

        # Inline edit form
        if st.session_state.get(f"editing_{i}"):
            with st.form(key=f"edit_form_{i}"):
                new_title = st.text_input("Title", value=t.title)
                new_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=t.duration_minutes)
                new_priority = st.selectbox("Priority", ["low", "medium", "high"], index=["low", "medium", "high"].index(t.priority))
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
st.caption("Calls Scheduler.build_master_schedule() across all pets.")

col_gen, col_reset = st.columns(2)
with col_gen:
    if st.button("Generate Schedule"):
        if not st.session_state.owner.pets:
            st.warning("Set an owner and pet first.")
        else:
            brain = Scheduler(owner=st.session_state.owner)
            schedule = brain.build_master_schedule()
            st.session_state.last_schedule = schedule
            st.session_state.last_plan_text = brain.explain_plan(schedule)

with col_reset:
    if st.button("Reset Schedule"):
        st.session_state.last_schedule = None
        st.session_state.last_plan_text = None
        # Mark all tasks as not completed so the scheduler can re-evaluate
        for pet in st.session_state.owner.pets:
            for task in pet.tasks:
                task.completed = False
        st.success("Schedule cleared. Tasks reset to not completed.")

if st.session_state.last_plan_text:
    st.text(st.session_state.last_plan_text)
