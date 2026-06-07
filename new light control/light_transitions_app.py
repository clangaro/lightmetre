import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"

TREATMENT_START = "09:00"
TREATMENT_END = "10:00"
BACKGROUND_START = "10:00"
BACKGROUND_END = "21:00"


# -----------------------------
# HELPERS
# -----------------------------
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

def extract_date_from_filename(fname: str) -> str | None:
    """Find YYYY-MM-DD anywhere in the filename."""
    m = DATE_RE.search(fname)
    return m.group(0) if m else None


def list_data_files(data_dir: str) -> list[str]:
    """Return csv files, including ones ending with .csv.locked."""
    if not os.path.isdir(data_dir):
        return []
    files = os.listdir(data_dir)
    return sorted([
        f for f in files
        if f.lower().endswith(".csv") or f.lower().endswith(".csv.locked")
    ])


def choose_time_column(df: pd.DataFrame) -> str | None:
    """Try common timestamp column names; otherwise return None."""
    candidates = ["timestamp", "Timestamp", "time", "Time", "datetime", "DateTime", "date_time"]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def load_file(file_name: str) -> pd.DataFrame:
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        return pd.DataFrame()

    df = pd.read_csv(file_path)

    # Try to auto-detect time column
    possible_time_cols = ["timestamp", "Timestamp", "time", "Time", "datetime", "DateTime"]

    time_col = None
    for col in df.columns:
        if col in possible_time_cols:
            time_col = col
            break

    # If none matched, assume first column is time
    if time_col is None:
        time_col = df.columns[0]

    # Convert to datetime and rename
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.rename(columns={time_col: "timestamp"})

    return df



def detect_sensor_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric columns except timestamp."""
    sensor_cols = []
    for c in df.columns:
        if c.lower() == "timestamp":
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            sensor_cols.append(c)
    return sensor_cols


def plot_with_shaded_regions(df: pd.DataFrame, sensor_col: str, date_str: str):
    fig, ax = plt.subplots()

    # Plot data
    ax.plot(df["timestamp"], df[sensor_col], label=sensor_col)

    # Shaded treatment time
    treatment_start = pd.to_datetime(f"{date_str} {TREATMENT_START}")
    treatment_end = pd.to_datetime(f"{date_str} {TREATMENT_END}")
    # shaded treatment time
    ax.axvspan(treatment_start, treatment_end, color="pink", alpha=0.2, label="Treatment Light")

    # Shaded background time
    background_start = pd.to_datetime(f"{date_str} {BACKGROUND_START}")
    background_end = pd.to_datetime(f"{date_str} {BACKGROUND_END}")
    ax.axvspan(background_start, background_end, color="blue", alpha=0.2, label="Background Light")



    ax.set_title(sensor_col)
    ax.set_ylabel("Light Intensity")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    ax.legend()

    plt.tight_layout()
    return fig


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("💡 Light Sensor Monitoring with Phase Detection")

# Check directory exists
if not os.path.isdir(DATA_DIR):
    st.error(f"DATA_DIR does not exist:\n{DATA_DIR}")
    st.stop()

all_files = list_data_files(DATA_DIR)

# Build mapping: date -> list of files
files_by_date: dict[str, list[str]] = {}
for f in all_files:
    d = extract_date_from_filename(f)
    if d is None:
        continue
    files_by_date.setdefault(d, []).append(f)

available_dates = sorted(files_by_date.keys())

if not available_dates:
    st.warning("No CSV files with a YYYY-MM-DD date in the filename were found.")
    st.write("Files seen in DATA_DIR:", all_files[:50])
    st.stop()

selected_date = st.selectbox("Select Date", available_dates)

# If multiple files per date, let user choose which one
date_files = files_by_date[selected_date]
selected_file = st.selectbox("Select File for that Date", date_files)

df = load_file(selected_file)


if df.empty:
    st.warning("This file loaded as empty.")
    st.stop()

if "timestamp" not in df.columns:
    st.error("No usable timestamp column was detected. I can fix this once you tell me the time column name.")
    st.dataframe(df.head(10))
    st.stop()

sensor_cols = detect_sensor_columns(df)

if not sensor_cols:
    st.warning("No numeric sensor columns detected in this file.")
    st.dataframe(df.head(10))
    st.stop()

st.subheader("📊 Sensor Plots with Treatment & Background Shading")
st.write("Detected sensor columns:", sensor_cols)

for sensor_col in sensor_cols:
    fig = plot_with_shaded_regions(df, sensor_col, selected_date)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)