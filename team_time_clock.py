import streamlit as st
from datetime import datetime
from pathlib import Path
import pandas as pd

st.set_page_config(
    page_title="Tessy's Team Time Clock",
    page_icon="⏱️",
    layout="centered"
)

LOG_FILE = Path("team_time_log.csv")

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

st.markdown("""
# ⏱️ Tessy's Team Time Clock
### Team Clock In / Clock Out System
**Tessy's Residential Cleaning Service**  
📞 925-349-5668
""")

st.info("One phone or iPad can be used per team. Select the team members working, then clock them in/out together.")

st.divider()

st.subheader("Job Information")

job_address = st.text_input("Job Address")
service_type = st.selectbox(
    "Service Type",
    ["Recurring Cleaning", "Deep Cleaning", "Move-In / Move-Out", "Window Washing", "Other"]
)

team_name = st.selectbox("Team", list(TEAMS.keys()) + ["Custom Team"])
default_team = TEAMS.get(team_name, [])

if team_name == "Custom Team":
    selected_employees = st.multiselect("Select Employees Working", EMPLOYEES)
else:
    selected_employees = st.multiselect(
        "Select Employees Working",
        EMPLOYEES,
        default=default_team
    )

notes = st.text_area("Notes", placeholder="Example: customer requested extras, missed punch, access issue, etc.")

st.divider()

def save_event(event_type):
    now = datetime.now()

    rows = []
    for employee in selected_employees:
        rows.append({
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%I:%M:%S %p"),
            "Timestamp": now.isoformat(timespec="seconds"),
            "Event": event_type,
            "Employee Name": employee,
            "Team": team_name,
            "Job Address": job_address,
            "Service Type": service_type,
            "Notes": notes
        })

    df_new = pd.DataFrame(rows)

    if LOG_FILE.exists():
        df_old = pd.read_csv(LOG_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(LOG_FILE, index=False)
    st.success(f"{event_type} saved for {len(selected_employees)} employee(s) at {now.strftime('%I:%M:%S %p')}")

def validate():
    if not job_address:
        st.error("Please enter the job address.")
        return False
    if not selected_employees:
        st.error("Please select at least one employee.")
        return False
    return True

st.subheader("Team Time Clock")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Clock In Team", use_container_width=True):
        if validate():
            save_event("Clock In")

    if st.button("🍽️ Lunch Start", use_container_width=True):
        if validate():
            save_event("Lunch Start")

with col2:
    if st.button("🔁 Lunch End", use_container_width=True):
        if validate():
            save_event("Lunch End")

    if st.button("🛑 Clock Out Team", use_container_width=True):
        if validate():
            save_event("Clock Out")

st.divider()

st.subheader("Time Log")

if LOG_FILE.exists():
    df = pd.read_csv(LOG_FILE)
    st.dataframe(df.sort_values(by=["Timestamp"], ascending=False), use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Time Log",
        data=csv_data,
        file_name="team_time_log.csv",
        mime="text/csv"
    )
else:
    st.write("No time records yet.")

st.divider()

st.subheader("Important Rules")
st.markdown("""
- Employees should clock in only when they arrive at the job site.
- Employees should clock out before leaving the job site.
- Lunch punches should be recorded accurately.
- Missed punches should be reported to a supervisor.
- Review time records before using for payroll.
""")

st.caption("Starter version saves to CSV. For multiple devices and long-term payroll tracking, upgrade to Google Sheets/database storage.")
