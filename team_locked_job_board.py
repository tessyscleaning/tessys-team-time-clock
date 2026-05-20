import streamlit as st
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import quote
import pandas as pd

st.set_page_config(page_title="Tessy's Team-Locked Job Board", page_icon="🧽", layout="centered")

LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")
JOBS_FILE = Path("daily_jobs.csv")
TIME_LOG_FILE = Path("team_time_log.csv")

ADMIN_PIN = "5668"
TEAM_PINS = {"Team 1": "1111", "Team 2": "2222", "Team 3": "3333"}

EMPLOYEES = [
    "Kenny G Galindo Gomez",
    "Iris L Rivas Martinez",
    "Yesenia Chavez",
    "Lidia I Figueroa Campos",
    "Olivia Rosales",
    "Yohana Beatriz Ticas Contreras",
]

TEAMS = {
    "Team 1": ["Kenny G Galindo Gomez", "Yesenia Chavez", "Yohana Beatriz Ticas Contreras"],
    "Team 2": ["Iris L Rivas Martinez", "Olivia Rosales"],
    "Team 3": ["Lidia I Figueroa Campos"],
}

SERVICE_TYPES = ["Recurring Cleaning", "Deep Cleaning", "Move-In / Move-Out", "Window Washing", "Other"]
JOB_COLUMNS = ["Date", "Start Time", "Client Name", "Address", "Service Type", "Team", "Estimated Hours", "Job Notes"]
TIME_COLUMNS = ["Date", "Time", "Timestamp", "Time Zone", "Event", "Employee Name", "Team", "Client Name", "Job Address", "Service Type", "Job Notes", "Employee Notes"]

def local_now():
    return datetime.now(LOCAL_TIMEZONE)

def load_jobs():
    if JOBS_FILE.exists():
        return pd.read_csv(JOBS_FILE)
    return pd.DataFrame(columns=JOB_COLUMNS)

def save_jobs(df):
    df.to_csv(JOBS_FILE, index=False)

def load_time_log():
    if TIME_LOG_FILE.exists():
        df = pd.read_csv(TIME_LOG_FILE)
        for col in TIME_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[TIME_COLUMNS]
    return pd.DataFrame(columns=TIME_COLUMNS)

def save_time_log(df):
    df.to_csv(TIME_LOG_FILE, index=False)

def save_time_event(event_type, employees, team, job_row, employee_notes):
    now = local_now()
    rows = []
    for employee in employees:
        rows.append({
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%I:%M:%S %p"),
            "Timestamp": now.isoformat(timespec="seconds"),
            "Time Zone": "America/Los_Angeles",
            "Event": event_type,
            "Employee Name": employee,
            "Team": team,
            "Client Name": job_row.get("Client Name", ""),
            "Job Address": job_row.get("Address", ""),
            "Service Type": job_row.get("Service Type", ""),
            "Job Notes": job_row.get("Job Notes", ""),
            "Employee Notes": employee_notes
        })
    final = pd.concat([load_time_log(), pd.DataFrame(rows)], ignore_index=True)
    save_time_log(final)

st.markdown("""
# 🧽 Tessy's Team Job Board
### Team-Locked Schedule + Clock In / Out
**Tessy's Residential Cleaning Service**  
📞 925-349-5668
""")
st.info("Times are recorded in California time: America/Los_Angeles.")
st.divider()

mode = st.radio("Login Type", ["Team Login", "Admin Login"], horizontal=True)

if mode == "Admin Login":
    pin = st.text_input("Admin PIN", type="password")
    if pin != ADMIN_PIN:
        st.warning("Enter admin PIN to manage schedules.")
        st.stop()

    st.success("Admin access granted.")
    page = st.sidebar.radio("Admin Menu", ["Add Jobs", "Manage Schedule", "Time Logs"])

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

    elif page == "Manage Schedule":
        st.header("Manage Schedule")
        jobs = load_jobs()
        if jobs.empty:
            st.write("No jobs added yet.")
            st.stop()

        filter_date = st.date_input("Filter by Date", value=date.today())
        filter_team = st.selectbox("Filter by Team", ["All Teams"] + list(TEAMS.keys()))

        filtered = jobs[jobs["Date"] == filter_date.strftime("%Y-%m-%d")]
        if filter_team != "All Teams":
            filtered = filtered[filtered["Team"] == filter_team]

        st.subheader("Filtered Jobs")
        st.dataframe(filtered, use_container_width=True)

        st.divider()
        st.subheader("Delete One Job")
        if filtered.empty:
            st.info("No jobs match this filter.")
        else:
            job_options = [(idx, f"{row['Date']} | {row['Start Time']} | {row['Team']} | {row['Client Name']} | {row['Address']}") for idx, row in filtered.iterrows()]
            selected_idx = st.selectbox("Select job to delete", options=[x[0] for x in job_options], format_func=lambda x: dict(job_options)[x])
            confirm_delete = st.checkbox("I understand this will delete the selected job.")
            if st.button("🗑️ Delete Selected Job", type="primary"):
                if confirm_delete:
                    jobs = jobs.drop(index=selected_idx).reset_index(drop=True)
                    save_jobs(jobs)
                    st.success("Selected job deleted. Refresh if needed.")
                else:
                    st.error("Please check the confirmation box first.")

        st.divider()
        st.subheader("Clear Schedule")
        col_a, col_b = st.columns(2)
        with col_a:
            confirm_clear_filtered = st.checkbox("Confirm clear filtered jobs")
            if st.button("🧹 Clear Filtered Jobs"):
                if confirm_clear_filtered:
                    jobs = jobs.drop(index=filtered.index).reset_index(drop=True)
                    save_jobs(jobs)
                    st.success("Filtered jobs cleared.")
                else:
                    st.error("Please confirm first.")
        with col_b:
            confirm_clear_all = st.checkbox("Confirm clear ALL jobs")
            if st.button("🚨 Clear ALL Jobs"):
                if confirm_clear_all:
                    save_jobs(pd.DataFrame(columns=JOB_COLUMNS))
                    st.success("All jobs cleared.")
                else:
                    st.error("Please confirm first.")

        st.download_button("⬇️ Download Full Schedule", data=jobs.to_csv(index=False).encode("utf-8"), file_name="daily_jobs.csv", mime="text/csv")

    elif page == "Time Logs":
        st.header("Time Logs")
        logs = load_time_log()

        if logs.empty:
            st.write("No time records yet.")
        else:
            filter_log_date = st.date_input("Filter Logs by Date", value=date.today())
            filter_log_team = st.selectbox("Filter Logs by Team", ["All Teams"] + list(TEAMS.keys()))

            filtered_logs = logs[logs["Date"] == filter_log_date.strftime("%Y-%m-%d")]
            if filter_log_team != "All Teams":
                filtered_logs = filtered_logs[filtered_logs["Team"] == filter_log_team]

            st.subheader("Filtered Time Logs")
            st.dataframe(filtered_logs.sort_values(by="Timestamp", ascending=False), use_container_width=True)

            st.download_button("⬇️ Download All Time Logs", data=logs.to_csv(index=False).encode("utf-8"), file_name="team_time_log.csv", mime="text/csv")

            st.divider()
            st.subheader("Delete One Time Log Entry")
            if filtered_logs.empty:
                st.info("No time logs match this filter.")
            else:
                log_options = []
                for idx, row in filtered_logs.iterrows():
                    label = f"{row['Date']} | {row['Time']} | {row['Event']} | {row['Employee Name']} | {row['Team']} | {row['Client Name']}"
                    log_options.append((idx, label))

                selected_log_idx = st.selectbox(
                    "Select time log entry to delete",
                    options=[x[0] for x in log_options],
                    format_func=lambda x: dict(log_options)[x]
                )

                confirm_log_delete = st.checkbox("I understand this will delete the selected time log.")
                if st.button("🗑️ Delete Selected Time Log"):
                    if confirm_log_delete:
                        logs = logs.drop(index=selected_log_idx).reset_index(drop=True)
                        save_time_log(logs)
                        st.success("Selected time log deleted. Refresh if needed.")
                    else:
                        st.error("Please check the confirmation box first.")

            st.divider()
            st.subheader("Clear Time Logs")
            col1, col2 = st.columns(2)

            with col1:
                confirm_clear_filtered_logs = st.checkbox("Confirm clear filtered time logs")
                if st.button("🧹 Clear Filtered Time Logs"):
                    if confirm_clear_filtered_logs:
                        logs = logs.drop(index=filtered_logs.index).reset_index(drop=True)
                        save_time_log(logs)
                        st.success("Filtered time logs cleared.")
                    else:
                        st.error("Please confirm first.")

            with col2:
                confirm_clear_all_logs = st.checkbox("Confirm clear ALL time logs")
                if st.button("🚨 Clear ALL Time Logs"):
                    if confirm_clear_all_logs:
                        save_time_log(pd.DataFrame(columns=TIME_COLUMNS))
                        st.success("All time logs cleared.")
                    else:
                        st.error("Please confirm first.")

else:
    st.header("Team Login")
    team = st.selectbox("Select Team", list(TEAM_PINS.keys()))
    pin = st.text_input("Team PIN", type="password")
    if pin != TEAM_PINS[team]:
        st.warning("Enter your team PIN to see your jobs.")
        st.stop()

    st.success(f"{team} access granted.")
    st.write("Current California time:", local_now().strftime("%A, %B %d, %Y — %I:%M:%S %p"))
    selected_date = st.date_input("Schedule Date", value=date.today())
    employees = st.multiselect("Employees Working", EMPLOYEES, default=TEAMS[team])

    jobs = load_jobs()
    if jobs.empty:
        st.warning("No jobs added yet.")
        st.stop()

    team_jobs = jobs[(jobs["Date"] == selected_date.strftime("%Y-%m-%d")) & (jobs["Team"] == team)]
    if team_jobs.empty:
        st.warning("No jobs found for your team/date.")
        st.stop()

    st.subheader("Your Team Jobs")
    options = [(idx, f"{row['Start Time']} — {row['Client Name']} — {row['Address']}") for idx, row in team_jobs.iterrows()]
    selected_idx = st.selectbox("Select Job", options=[x[0] for x in options], format_func=lambda x: dict(options)[x])
    job = jobs.loc[selected_idx]

    st.markdown(f"""
    ### Selected Job
    **Client:** {job['Client Name']}  
    **Address:** {job['Address']}  
    **Service:** {job['Service Type']}  
    **Estimated Hours:** {job['Estimated Hours']}  
    **Notes:** {job['Job Notes']}
    """)

    encoded_address = quote(str(job["Address"]))
    google_maps = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
    apple_maps = f"https://maps.apple.com/?q={encoded_address}"

    col_map1, col_map2 = st.columns(2)
    with col_map1:
        st.markdown(f"[🗺️ Open in Google Maps]({google_maps})")
    with col_map2:
        st.markdown(f"[🍎 Open in Apple Maps]({apple_maps})")

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
                st.success("Clock In saved with California time.")
        if st.button("🍽️ Lunch Start", use_container_width=True):
            if valid():
                save_time_event("Lunch Start", employees, team, job, employee_notes)
                st.success("Lunch Start saved with California time.")
    with col2:
        if st.button("🔁 Lunch End", use_container_width=True):
            if valid():
                save_time_event("Lunch End", employees, team, job, employee_notes)
                st.success("Lunch End saved with California time.")
        if st.button("🛑 Clock Out Team", use_container_width=True):
            if valid():
                save_time_event("Clock Out", employees, team, job, employee_notes)
                st.success("Clock Out saved with California time.")

st.divider()
st.caption("Starter version uses CSV storage. Times are saved in America/Los_Angeles.")
