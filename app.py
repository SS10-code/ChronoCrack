import streamlit as st
from datetime import date
from scheduler import generate_schedule
from query_deepseek import query_deepseek
import pandas as pd
import altair as alt
import time

# set app layout
st.set_page_config(page_title="ChronoCrack", layout="centered")
st.markdown("<style>.stApp {background-color: #ffc95c;} h1,h2,h3{color:black;}</style>", unsafe_allow_html=True) # b&w both so saturate bg

# mark session state
if "page" not in st.session_state: st.session_state.page = 1

if "assignments" not in st.session_state: st.session_state.assignments = []

if "availability" not in st.session_state:
    st.session_state.availability = {"Monday": 120, "Tuesday": 120, "Wednesday": 120, "Thursday": 120, "Friday": 120,"Saturday": 180, "Sunday": 180}

if "loading" not in st.session_state: st.session_state.loading = False

if "edit_index" not in st.session_state: st.session_state.edit_index = -1

# main Title
st.title("ChronoCrack")

# loading spin
if st.session_state.loading:
    with st.spinner("Loading"):
        time.sleep(0.8)
    st.session_state.loading = False
    st.rerun()

# Sidebar explainer w/ ai
with st.sidebar.expander("StudyBuddy Mode", expanded=False):
    st.write("Ask StudyBuddy for help understanding a topic")
    api_key = "yor-API-key-here" # add your own API call Here
    user_prompt = st.text_area("Ask a question", placeholder="e.g. Explain photosynthesis")

    if st.button("Ask"):
        
        if not api_key or not user_prompt:
            st.warning("Please enter both API key and your question")
        else:
            
            with st.spinner("StudyBuddy is thinking..."):
                
                try:
                    response = query_deepseek(user_prompt, api_key)
                    st.markdown(f"**StudyBuddy:** {response}")
                except Exception as e:
                    st.error(f"Error: {e}")

# pages for time management

# add/edit tasks
if st.session_state.page == 1:
    st.header("Step 1: Add or Edit Assignments")

    # load old vals on edit
    if st.session_state.edit_index != -1:
        a = st.session_state.assignments[st.session_state.edit_index]
        default_course, default_task, default_due_date = a["course"], a["task"], a["due_date"]
        default_hours, default_minutes = a["minutes_required"] // 60, a["minutes_required"] % 60
    
    else:
        default_course = default_task = ""
        default_due_date = date.today()
        default_hours, default_minutes = 0, 15

    # new task
    with st.form("assignment_form", clear_on_submit=False):
        course = st.text_input("Course Name", value=default_course)
        task = st.text_input("Assignment Title", value=default_task)
        due_date = st.date_input("Due Date", min_value=date.today(), value=default_due_date)
        col1, col2 = st.columns(2)
        
        with col1:
            hours_required = st.number_input("Estimated Time - Hours", min_value=0, max_value=100, value=default_hours)
        
        with col2:
            minutes_required = st.number_input("Estimated Time - Minutes", min_value=0, max_value=59, value=default_minutes)
        
        submitted = st.form_submit_button("Save Assignment" if st.session_state.edit_index != -1 else "Add Assignment")

    # save/ resave task
    if submitted:
        total_minutes = hours_required * 60 + minutes_required

        if not course or not task:
            st.warning("Please enter both course and assignment title")

        elif total_minutes == 0:
            st.warning("Estimated time cannot be zero")

        else:
            new_assignment = {
                "course": course,
                "task": task,
                "due_date": due_date,
                "minutes_required": total_minutes
            }
            if st.session_state.edit_index == -1:
                st.session_state.assignments.append(new_assignment)
                st.success(f"Added: {task} ({total_minutes} minutes)")

            else:
                st.session_state.assignments[st.session_state.edit_index] = new_assignment
                st.success(f"Updated: {task} ({total_minutes} minutes)")
                st.session_state.edit_index = -1

            st.rerun()

    # Sshow all tasks
    if st.session_state.assignments:
        st.subheader("Your Assignments")

        for i, a in enumerate(st.session_state.assignments):
            c1, c2, c3, c4 = st.columns([4, 4, 3, 1])
            c1.write(a["course"])
            c2.write(a["task"])
            c3.write(f"{a['minutes_required'] // 60} hr {a['minutes_required'] % 60} min")

            if c4.button("Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()

# weekly availability
elif st.session_state.page == 2:

    st.header("Step 2: Set Weekly Availability")

    with st.form("availability_form"):

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        availability_inputs = {}
        st.write("Enter availability for each day (Hours and Minutes):")

        for day in days:
            c1, c2 = st.columns(2)
            with c1:
                hours = st.number_input(f"{day} - Hours", min_value=0, max_value=12,
                                        value=st.session_state.availability.get(day, 0) // 60, key=f"{day}_hours")
            with c2:
                minutes = st.number_input(f"{day} - Minutes", min_value=0, max_value=59,
                                          value=st.session_state.availability.get(day, 0) % 60, key=f"{day}_minutes")
            
            availability_inputs[day] = hours * 60 + minutes


        save_avail = st.form_submit_button("Save Availability")

    if save_avail:
        st.session_state.availability = availability_inputs
        st.success("Weekly availability updated")

    # show table
    readable_avail = {
        day: f"{m // 60} hr {m % 60} min" if m % 60 else f"{m // 60} hr"
        for day, m in st.session_state.availability.items()
    }
    st.table(pd.DataFrame.from_dict(readable_avail, orient='index', columns=["Available Time"]))

# get study plan
elif st.session_state.page == 3:
    st.header("Step 3: Generate Study Plan")

    if st.button("Generate Study Plan"):
        if not st.session_state.assignments:
            st.warning("Add at least one assignment first")

        else:
            today = pd.to_datetime(date.today())
            total_needed = sum(a["minutes_required"] for a in st.session_state.assignments)
            latest_due = max(a["due_date"] for a in st.session_state.assignments)
            days_list = pd.date_range(start=today, end=latest_due)

            total_available = sum(
                st.session_state.availability.get(d.strftime("%A"), 0)
                for d in days_list
            )

            if total_needed > total_available:
                st.error(f"Not enough time Need {total_needed} minutes, only {total_available} available.")

            else:
                try:

                    with st.spinner("Creating your plan"):
                        schedule_df = generate_schedule(
                            assignments=st.session_state.assignments,
                            availability=st.session_state.availability,
                            use_minutes=True
                        )
                    st.success("Study Plan Generated")
                    st.subheader("Your Study Schedule")
                    st.dataframe(schedule_df[["Date", "Weekday", "Course", "Assignment", "Time"]])

                    # show chart
                    st.subheader("Time Distribution by Day & Assignment")
                    chart = alt.Chart(schedule_df).mark_bar(size=40).encode(
                        x=alt.X('yearmonthdate(Date):T', title='Date'),
                        y=alt.Y('Minutes:Q', title='Time (mins)'),
                        color='Assignment:N',
                        tooltip=['Assignment', 'Course', 'Time', 'Date']
                    ).properties(width=700, height=400).configure_axis(labelAngle=-45)
                    st.altair_chart(chart, use_container_width=True)

                except Exception as e:
                    st.error(f"Error: {e}")

# Nav control
st.markdown("---")
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.session_state.page > 1:

        if st.button("Previous"):
            st.session_state.page -= 1
            st.session_state.loading = True
            st.rerun()

with c3:
    if st.session_state.page < 3:
        if st.button("Next"):
            st.session_state.page += 1
            st.session_state.loading = True
            st.rerun()
