import streamlit as st
from datetime import datetime, date
from pathlib import Path
import pandas as pd

st.set_page_config(
    page_title="Tessy's Team-Locked Job Board",
    page_icon="🧽",
    layout="centered"
)

JOBS_FILE = Path("daily_jobs.csv")
TIME_LOG_FILE = Path("team_time_log.csv")

ADMIN_PIN = "5668"

TEAM_PINS = {
    "Team 1": "1111",
    "Team 2": "2222",
    "Team 3": "3333",
}

EMPLOYEES = [
    "Employee 1",
    "Employee 2",
    "Employee 3",
    "Employee 4",
    "Employee 5",
    "Employee 6",
    "Employee 7",
]

TEAMS = {
    "Team 1": ["Employee 1", "Employee 2", "Employee 3"],
    "Team 2": ["Employee 4", "Employee 5"],
    "Team 3": ["Employee 6", "Employee 7"],
}

SERVICE_TYPES = [
    "Recurring Cleaning",
    "Deep Cleaning",
    "Move-In / Move-Out",
    "Window Washing",
    "Other"
]

JOB_COLUMNS = [
    "Date", "Start Time", "Client Name", "Address",
    "Service Type", "Team", "Estimated Hours", "Job Notes"
]

TIME_COLUMNS = [
    "Date", "Time", "Timestamp", "Event", "Employee Name",
    "Team", "Client Name", "Job Address", "Service Type",
    "Job Notes", "Employee Notes"
]

def load_jobs():
    if JOBS_FILE.exists():
        return pd.read_csv(JOBS_FILE)
    return pd.DataFrame(columns=JOB_COLUMNS)

def save_jobs(df):
    df.to_csv(JOBS_FILE, index=False)

def load_time_log():
    if TIME_LOG_FILE.exists():
        return pd.read_csv(TIME_LOG_FILE)
    return pd.DataFrame(columns=TIME_COLUMNS)

def save_time_event(event_type, employees, team, job_row, employee_notes):
    now = datetime.now()
    rows = []

    for employee in employees:
        rows.append({
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%I:%M:%S %p"),
            "Timestamp": now.isoformat(timespec="seconds"),
            "Event": event_type,
            "Employee Name": employee,
            "Team": team,
            "Client Name": job_row.get("Client Name", ""),
            "Job Address": job_row.get("Address", ""),
            "Service Type": job_row.get("Service Type", ""),
            "Job Notes": job_row.get("Job Notes", ""),
            "Employee Notes": employee_notes
        })

    old = load_time_log()
    new = pd.DataFrame(rows)
    final = pd.concat([old, new], ignore_index=True)
    final.to_csv(TIME_LOG_FILE, index=False)

st.markdown("""
# 🧽 Tessy's Team Job Board
### Team-Locked Schedule + Clock In / Out
**Tessy's Residential Cleaning Service**  
📞 925-349-5668
""")

st.info("Employees use their team PIN and only see their own team's jobs. Admin can add schedules and view all logs.")

st.divider()

mode = st.radio("Login Type", ["Team Login", "Admin Login"], horizontal=True)

if mode == "Admin Login":
    pin = st.text_input("Admin PIN", type="password")

    if pin != ADMIN_PIN:
        st.warning("Enter admin PIN to manage schedules.")
        st.stop()

    st.success("Admin access granted.")

    page = st.sidebar.radio("Admin Menu", ["Add Jobs", "View Schedule", "Time Logs"])

    if page == "Add Jobs":
        st.header("Add Daily Job")

        with st.form("add_job"):
            job_date = st.date_input("Job Date", value=date.today())
            start_time = st.text_input("Start Time", placeholder="Example: 8:00 AM")
            client_name = st.text_input("Client Name")
            address = st.text_input("Address")
            service_type = st.selectbox("Service Type", SERVICE_TYPES)
            team = st.selectbox("Assign Team", list(TEAMS.keys()))
            estimated_hours = st.number_input("Estimated Hours", min_value=0.0, value=2.0, step=0.5)
            job_notes = st.text_area("Job Notes", placeholder="Pets, gate code, priority areas, supplies, etc.")
            submitted = st.form_submit_button("➕ Add Job")

            if submitted:
                if not start_time or not client_name or not address:
                    st.error("Please enter start time, client name, and address.")
                else:
                    df = load_jobs()
                    row = {
                        "Date": job_date.strftime("%Y-%m-%d"),
                        "Start Time": start_time,
                        "Client Name": client_name,
                        "Address": address,
                        "Service Type": service_type,
                        "Team": team,
                        "Estimated Hours": estimated_hours,
                        "Job Notes": job_notes
                    }
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                    save_jobs(df)
                    st.success(f"Job added for {team}: {client_name}")

        st.subheader("Current Schedule")
        st.dataframe(load_jobs(), use_container_width=True)

    elif page == "View Schedule":
        st.header("Full Schedule")
        jobs = load_jobs()
        if jobs.empty:
            st.write("No jobs added yet.")
        else:
            filter_date = st.date_input("Date", value=date.today())
            filter_team = st.selectbox("Team", ["All Teams"] + list(TEAMS.keys()))
            df = jobs[jobs["Date"] == filter_date.strftime("%Y-%m-%d")]
            if filter_team != "All Teams":
                df = df[df["Team"] == filter_team]
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "⬇️ Download Schedule",
                data=jobs.to_csv(index=False).encode("utf-8"),
                file_name="daily_jobs.csv",
                mime="text/csv"
            )

    elif page == "Time Logs":
        st.header("Time Logs")
        logs = load_time_log()
        if logs.empty:
            st.write("No time records yet.")
        else:
            st.dataframe(logs.sort_values(by="Timestamp", ascending=False), use_container_width=True)
            st.download_button(
                "⬇️ Download Time Log",
                data=logs.to_csv(index=False).encode("utf-8"),
                file_name="team_time_log.csv",
                mime="text/csv"
            )

else:
    st.header("Team Login")

    team = st.selectbox("Select Team", list(TEAM_PINS.keys()))
    pin = st.text_input("Team PIN", type="password")

    if pin != TEAM_PINS[team]:
        st.warning("Enter your team PIN to see your jobs.")
        st.stop()

    st.success(f"{team} access granted.")

    selected_date = st.date_input("Schedule Date", value=date.today())

    employees = st.multiselect(
        "Employees Working",
        EMPLOYEES,
        default=TEAMS[team]
    )

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No jobs added yet.")
        st.stop()

    team_jobs = jobs[
        (jobs["Date"] == selected_date.strftime("%Y-%m-%d")) &
        (jobs["Team"] == team)
    ]

    if team_jobs.empty:
        st.warning("No jobs found for your team/date.")
        st.stop()

    st.subheader("Your Team Jobs")

    options = []
    for idx, row in team_jobs.iterrows():
        label = f"{row['Start Time']} — {row['Client Name']} — {row['Address']}"
        options.append((idx, label))

    selected_idx = st.selectbox(
        "Select Job",
        options=[x[0] for x in options],
        format_func=lambda x: dict(options)[x]
    )

    job = jobs.loc[selected_idx]

    st.markdown(f"""
    ### Selected Job
    **Client:** {job['Client Name']}  
    **Address:** {job['Address']}  
    **Service:** {job['Service Type']}  
    **Estimated Hours:** {job['Estimated Hours']}  
    **Notes:** {job['Job Notes']}
    """)

    map_query = str(job["Address"]).replace(" ", "+")
    st.markdown(f"[🗺️ Open in Google Maps](https://www.google.com/maps/search/?api=1&query={map_query})")

    employee_notes = st.text_area("Employee Notes", placeholder="Add notes for this job, if needed.")

    st.divider()

    def valid():
        if not employees:
            st.error("Please select at least one employee.")
            return False
        return True

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Clock In Team", use_container_width=True):
            if valid():
                save_time_event("Clock In", employees, team, job, employee_notes)
                st.success("Clock In saved.")

        if st.button("🍽️ Lunch Start", use_container_width=True):
            if valid():
                save_time_event("Lunch Start", employees, team, job, employee_notes)
                st.success("Lunch Start saved.")

    with col2:
        if st.button("🔁 Lunch End", use_container_width=True):
            if valid():
                save_time_event("Lunch End", employees, team, job, employee_notes)
                st.success("Lunch End saved.")

        if st.button("🛑 Clock Out Team", use_container_width=True):
            if valid():
                save_time_event("Clock Out", employees, team, job, employee_notes)
                st.success("Clock Out saved.")

st.divider()
st.caption("Starter version uses CSV storage. For long-term multi-device use, upgrade to Google Sheets or a database.")
