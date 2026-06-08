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


PINK_BG_FIG = "#fff5f8"
PINK_BG_AX = "#ffffff"
PINK_LINE = "#c2185b"
PINK_TREATMENT = "#ff4d8d"
PINK_BACKGROUND = "#b48ce0"
PINK_SPINE = "#d6336c"
PINK_TEXT = "#3d0a1e"


def plot_with_shaded_regions(df: pd.DataFrame, sensor_col: str, date_str: str):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor(PINK_BG_FIG)
    ax.set_facecolor(PINK_BG_AX)

    ax.plot(
        df["timestamp"], df[sensor_col],
        label=sensor_col, color=PINK_LINE, linewidth=1.8,
    )

    treatment_start = pd.to_datetime(f"{date_str} {TREATMENT_START}")
    treatment_end = pd.to_datetime(f"{date_str} {TREATMENT_END}")
    ax.axvspan(treatment_start, treatment_end, color=PINK_TREATMENT, alpha=0.28, label="Treatment Light")

    background_start = pd.to_datetime(f"{date_str} {BACKGROUND_START}")
    background_end = pd.to_datetime(f"{date_str} {BACKGROUND_END}")
    ax.axvspan(background_start, background_end, color=PINK_BACKGROUND, alpha=0.22, label="Background Light")

    ax.set_title(sensor_col, color=PINK_TEXT, fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Light Intensity", color=PINK_TEXT)
    ax.tick_params(colors=PINK_TEXT)
    for spine in ax.spines.values():
        spine.set_color(PINK_SPINE)
        spine.set_linewidth(1.2)
    ax.grid(True, color="#ffd6e4", linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    leg = ax.legend(frameon=True, facecolor=PINK_BG_FIG, edgecolor=PINK_SPINE, labelcolor=PINK_TEXT)
    for txt in leg.get_texts():
        txt.set_color(PINK_TEXT)

    plt.tight_layout()
    return fig


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Light Monitoring", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, .stSelectbox label {
        font-family: 'Quicksand', sans-serif !important;
        color: #3d0a1e !important;
    }

    .stApp {
        background: linear-gradient(160deg, #fff5f8 0%, #ffe0ec 60%, #ffc6dc 100%);
    }

    /* hide default top bar / hamburger / footer for a cleaner look */
    #MainMenu, footer, header {visibility: hidden;}

    .hero {
        background: linear-gradient(135deg, #ff8fb7 0%, #d6336c 100%);
        padding: 28px 36px;
        border-radius: 20px;
        margin-bottom: 28px;
        box-shadow: 0 8px 24px rgba(214, 51, 108, 0.25);
        color: white;
    }
    .hero h1 {
        margin: 0;
        font-family: 'Quicksand', sans-serif;
        font-weight: 700;
        font-size: 2.0rem;
        color: white;
        letter-spacing: 0.3px;
    }
    .hero p {
        margin: 6px 0 0;
        font-size: 0.95rem;
        opacity: 0.92;
        color: white;
    }

    .card {
        background: #ffffff;
        border-radius: 18px;
        padding: 18px 22px;
        margin-bottom: 22px;
        box-shadow: 0 4px 18px rgba(214, 51, 108, 0.12);
        border: 1px solid #ffd6e4;
    }
    .card h3 {
        margin-top: 0;
        color: #d6336c;
        font-weight: 700;
    }

    /* selectbox prettification */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #f48fb1 !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #d6336c !important;
    }

    /* subtle pink scrollbar */
    ::-webkit-scrollbar {width: 10px;}
    ::-webkit-scrollbar-thumb {background: #f48fb1; border-radius: 10px;}
    ::-webkit-scrollbar-track {background: #fff5f8;}
    </style>

    <div class="hero">
      <h1>Light Sensor Monitoring with Phase Detection</h1>
      <p>Daily traces with treatment and background windows shaded for context.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

available_dates = sorted(files_by_date.keys(), reverse=True)

if not available_dates:
    st.warning("No CSV files with a YYYY-MM-DD date in the filename were found.")
    st.write("Files seen in DATA_DIR:", all_files[:50])
    st.stop()

st.markdown('<h3 style="color:#d6336c; font-weight:700; margin-bottom:8px;">Select a recording</h3>', unsafe_allow_html=True)
col_date, col_file = st.columns(2)
with col_date:
    selected_date = st.selectbox("Date", available_dates)

date_files = files_by_date[selected_date]
with col_file:
    selected_file = st.selectbox("File", date_files)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

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

st.markdown(
    f"""
    <h3 style="color:#d6336c; font-weight:700; margin-top:8px; margin-bottom:4px;">
      Sensor traces for {selected_date}
    </h3>
    <p style="color:#3d0a1e; opacity:0.7; margin-top:0;">
      Pink shading = treatment window ({TREATMENT_START}–{TREATMENT_END}) ·
      Lavender shading = background window ({BACKGROUND_START}–{BACKGROUND_END}) ·
      Sensors: {", ".join(sensor_cols)}
    </p>
    """,
    unsafe_allow_html=True,
)

for sensor_col in sensor_cols:
    with st.container():
        fig = plot_with_shaded_regions(df, sensor_col, selected_date)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)