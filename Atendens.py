import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# Constants
CSV_FILE = "attendance_records.csv"
CSV_FIELDS = ["Student Name", "Date", "Time", "Status"]

# Utility Functions
def load_data():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=CSV_FIELDS)
        df.to_csv(CSV_FILE, index=False)
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def add_student(name):
    df = load_data()
    if name not in df["Student Name"].unique():
        # Add a dummy row to register student (no attendance yet)
        new_row = {"Student Name": name, "Date": "", "Time": "", "Status": ""}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        return True
    return False

def mark_attendance(name, status):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    df = load_data()
    # Check if attendance already marked for today
    already_marked = (
        (df["Student Name"] == name) &
        (df["Date"] == date_str) &
        (df["Status"].isin(["Present", "Absent"]))
    ).any()
    if already_marked:
        return False  # Attendance already marked
    new_row = {
        "Student Name": name,
        "Date": date_str,
        "Time": time_str,
        "Status": status
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    return True  # Attendance marked

def get_students():
    df = load_data()
    students = df["Student Name"].dropna().unique()
    students = [s for s in students if s.strip() != ""]
    return sorted(students)

def get_attendance_history(name):
    df = load_data()
    history = df[(df["Student Name"] == name) & (df["Date"].notna()) & (df["Date"] != "")]
    return history

def attendance_stats():
    df = load_data()
    df = df[df["Date"].notna() & (df["Date"] != "")]
    if df.empty:
        return pd.DataFrame(columns=["Student Name", "Present", "Absent", "Attendance %"])
    stats = df.groupby(["Student Name", "Status"]).size().unstack(fill_value=0)
    stats["Present"] = stats.get("Present", 0)
    stats["Absent"] = stats.get("Absent", 0)
    stats["Attendance %"] = stats["Present"] / (stats["Present"] + stats["Absent"]) * 100
    stats = stats.reset_index()
    return stats[["Student Name", "Present", "Absent", "Attendance %"]]

def attendance_stats_by_month(month, year):
    df = load_data()
    df = df[df["Date"].notna() & (df["Date"] != "")]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].dt.month == month]
    df = df[df["Date"].dt.year == year]
    if df.empty:
        return pd.DataFrame(columns=["Student Name", "Present", "Absent", "Attendance %"])
    stats = df.groupby(["Student Name", "Status"]).size().unstack(fill_value=0)
    stats["Present"] = stats.get("Present", 0)
    stats["Absent"] = stats.get("Absent", 0)
    stats["Attendance %"] = stats["Present"] / (stats["Present"] + stats["Absent"]) * 100
    stats = stats.reset_index()
    return stats[["Student Name", "Present", "Absent", "Attendance %"]]

def attendance_stats_by_year(year):
    df = load_data()
    df = df[df["Date"].notna() & (df["Date"] != "")]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].dt.year == year]
    if df.empty:
        return pd.DataFrame(columns=["Student Name", "Present", "Absent", "Attendance %"])
    stats = df.groupby(["Student Name", "Status"]).size().unstack(fill_value=0)
    stats["Present"] = stats.get("Present", 0)
    stats["Absent"] = stats.get("Absent", 0)
    stats["Attendance %"] = stats["Present"] / (stats["Present"] + stats["Absent"]) * 100
    stats = stats.reset_index()
    return stats[["Student Name", "Present", "Absent", "Attendance %"]]

def get_month_year_options():
    df = load_data()
    df = df[df["Date"].notna() & (df["Date"] != "")]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    months = sorted(df["Date"].dt.month.unique())
    years = sorted(df["Date"].dt.year.unique())
    return months, years

def validate_student_name(name):
    return name and isinstance(name, str) and name.strip() != ""

def import_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        if set(CSV_FIELDS).issubset(df.columns):
            orig_df = load_data()
            combined_df = pd.concat([orig_df, df], ignore_index=True).drop_duplicates()
            save_data(combined_df)
            return True, "Import successful."
        else:
            return False, "CSV schema mismatch."
    except Exception as e:
        return False, f"Import failed: {e}"

def export_csv():
    df = load_data()
    return df.to_csv(index=False).encode('utf-8')

def delete_attendance_record(student_name, date, time, status):
    df = load_data()
    # Remove the record matching all fields
    df = df[~(
        (df["Student Name"] == student_name) &
        (df["Date"] == date) &
        (df["Time"] == time) &
        (df["Status"] == status)
    )]
    save_data(df)

# Streamlit UI
st.set_page_config(page_title="Atendens - Student Attendance Tracker", layout="wide")
st.title("🎓 Atendens: Student Attendance Management")

tab1, tab2, tab3, tab4 = st.tabs(["Register/Manage Students", "Mark Attendance", "Student Dashboard", "Export/Import"])

with tab1:
    st.header("Register New Student")
    new_student = st.text_input("Enter student name")
    if st.button("Add Student"):
        if validate_student_name(new_student):
            if add_student(new_student.strip()):
                st.success(f"Student '{new_student}' added.")
            else:
                st.warning("Student already exists.")
        else:
            st.error("Invalid student name.")

    st.subheader("Registered Students")
    students = get_students()
    st.write(pd.DataFrame({"Student Name": students}))

with tab2:
    st.header("Mark Attendance")
    students = get_students()
    if students:
        selected_student = st.selectbox("Select student", students)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark Present"):
                success = mark_attendance(selected_student, "Present")
                if success:
                    st.success(f"Marked '{selected_student}' as Present.")
                else:
                    st.warning(f"Attendance for '{selected_student}' already marked today.")
        with col2:
            if st.button("Mark Absent"):
                success = mark_attendance(selected_student, "Absent")
                if success:
                    st.warning(f"Marked '{selected_student}' as Absent.")
                else:
                    st.warning(f"Attendance for '{selected_student}' already marked today.")
    else:
        st.info("No students registered yet.")

    st.subheader("Today's Attendance")
    df = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = df[df["Date"] == today]
    st.dataframe(today_attendance[CSV_FIELDS])

with tab3:
    st.header("Student Attendance Dashboard")
    students = get_students()
    selected_student = st.selectbox("Select student to view history", students)
    months, years = get_month_year_options()
    st.subheader("Filter Attendance By")
    col_month, col_year = st.columns(2)
    # Set default values for selectboxes if lists are not empty
    default_month = months[0] if months else None
    default_year = years[0] if years else None
    with col_month:
        selected_month = st.selectbox(
            "Month", months, format_func=lambda m: datetime(1900, m, 1).strftime('%B'),
            index=0 if months else None
        )
    with col_year:
        selected_year = st.selectbox(
            "Year", years,
            index=0 if years else None
        )
    if selected_student and selected_month is not None and selected_year is not None:
        history = get_attendance_history(selected_student)
        history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
        filtered_history = history[
            (history["Date"].dt.month == selected_month) &
            (history["Date"].dt.year == selected_year)
        ]
        month_name = datetime(1900, selected_month, 1).strftime('%B') if selected_month else ""
        st.subheader(f"Attendance History for {selected_student} ({month_name} {selected_year})")
        # Show table and allow selection for deletion
        if not filtered_history.empty:
            filtered_history_display = filtered_history[CSV_FIELDS].reset_index(drop=True)
            selected_row = st.selectbox(
                "Select a record to delete",
                filtered_history_display.index,
                format_func=lambda i: f"{filtered_history_display.loc[i, 'Date'].strftime('%Y-%m-%d')} {filtered_history_display.loc[i, 'Time']} - {filtered_history_display.loc[i, 'Status']}"
            )
            st.dataframe(filtered_history_display)
            if st.button("Delete Selected Record"):
                rec = filtered_history_display.loc[selected_row]
                delete_attendance_record(
                    student_name=rec["Student Name"],
                    date=rec["Date"].strftime('%Y-%m-%d') if pd.notnull(rec["Date"]) else "",
                    time=rec["Time"],
                    status=rec["Status"]
                )
                st.success("Record deleted. Please refresh to see changes.")
        else:
            st.info("No attendance records for this student in the selected month/year.")
        present_count = (filtered_history["Status"] == "Present").sum()
        absent_count = (filtered_history["Status"] == "Absent").sum()
        total = present_count + absent_count
        percent = (present_count / total * 100) if total > 0 else 0
        st.metric("Present", present_count)
        st.metric("Absent", absent_count)
        st.metric("Attendance %", f"{percent:.2f}%")
        st.subheader("Attendance Over Time")
        if not filtered_history.empty:
            chart_data = filtered_history.groupby("Date")["Status"].apply(lambda x: (x == "Present").sum()).reset_index()
            chart_data.columns = ["Date", "Present Count"]
            st.line_chart(chart_data.set_index("Date"))
    else:
        st.info("Select a student and valid month/year to view dashboard.")

    st.subheader("Overall Attendance Statistics")
    stats = attendance_stats()
    st.dataframe(stats)

    if selected_month is not None and selected_year is not None:
        st.subheader("Monthly Attendance Statistics")
        stats_month = attendance_stats_by_month(selected_month, selected_year)
        st.dataframe(stats_month)

        st.subheader("Yearly Attendance Statistics")
        stats_year = attendance_stats_by_year(selected_year)
        st.dataframe(stats_year)

with tab4:
    st.header("Export Attendance Records")
    st.download_button(
        label="Download CSV",
        data=export_csv(),
        file_name="attendance_records_export.csv",
        mime="text/csv"
    )

    st.header("Import Attendance Records")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        success, msg = import_csv(uploaded_file)
        if success:
            st.success(msg)
        else:
            st.error(msg)

# Footer
st.markdown("---")
st.markdown("© 2025 Atendens | Attendance Management System | Powered by Streamlit")