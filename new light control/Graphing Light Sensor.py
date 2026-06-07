
import os
import time
import serial
import matplotlib
from datetime import datetime
from collections import deque

# -----------------------
# Plot backend (forces a real pop-out window in most PyCharm setups)
# -----------------------
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # noqa: E402


# =======================
# CONFIG
# =======================

# Serial
BAUD_RATE = 9600
SERIAL_PORT = "COM21"
SERIAL_TIMEOUT_SEC = 2

# Data output
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"
CSV_PREFIX = ""  # e.g. "12C_" -> YYYY-MM-DD_12C_light_data.csv

# CSV logging frequency
# - True  -> write every valid sample line to CSV (best for full resolution)
# - False -> write snapshots only every OUTPUT_INTERVAL_SEC
WRITE_EVERY_SAMPLE = False
OUTPUT_INTERVAL_SEC = 600  # 10 minutes (only used if WRITE_EVERY_SAMPLE = False)

# Real-time plotting
MAX_POINTS = 600000           # points retained on screen
PLOT_PAUSE_SEC = 0.05      # GUI refresh delay
Y_LIM = (0, 1023)          # adjust if your ADC differs

SENSOR_LABELS = ["sensor1", "sensor2", "sensor3", "sensor4"]

# Debug
PRINT_RAW = True           # prints every raw serial line (spammy). Set to False once confirmed.
PRINT_MALFORMED = True     # prints lines that still cannot be parsed


# =======================
# Helper functions
# =======================

def ensure_data_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def current_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def timestamp_full_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def csv_path_for_today() -> str:
    # e.g. 2026-02-23_light_data.csv
    date = current_date_str()
    middle = f"_{CSV_PREFIX}" if CSV_PREFIX else "_"
    return os.path.join(DATA_DIR, f"{date}{middle}light_data.csv")


def write_csv_header_if_needed(csv_file: str) -> None:
    if not os.path.exists(csv_file):
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            f.write("timestamp," + ",".join(SENSOR_LABELS) + "\n")
            f.flush()


def lock_previous_csv(old_csv_file: str) -> None:
    pass

def parse_sensor_line(line: str):
    """
    Accepts common Arduino output formats, e.g.:
      "123,456,789,12"
      "123 456 789 12"
      "S1:123,S2:456,S3:789,S4:12"
      "A=123 B=456 C=789 D=12"
    Returns: list[int] length 4, or None if not parseable.
    """
    # Keep digits, commas, spaces, minus signs; turn other separators into spaces
    cleaned_chars = []
    for ch in line:
        if ch.isdigit() or ch in {",", " ", "-"}:
            cleaned_chars.append(ch)
        else:
            cleaned_chars.append(" ")
    cleaned = "".join(cleaned_chars)

    # Normalise commas to spaces then split
    cleaned = cleaned.replace(",", " ")
    parts = [p for p in cleaned.split() if p]

    if len(parts) < 4:
        return None

    # Take the last 4 numbers found (in case there are extra tokens)
    try:
        vals = list(map(int, parts[-4:]))
    except ValueError:
        return None

    return vals


# =======================
# Main
# =======================

def main():
    ensure_data_dir(DATA_DIR)

    # Serial connect
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT_SEC)
        print(f"✅ Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
    except Exception as e:
        print(f"❌ Serial error: {e}")
        raise SystemExit(1)

    # CSV init
    current_csv = csv_path_for_today()
    write_csv_header_if_needed(current_csv)
    last_date = current_date_str()

    # Snapshot timer (used if WRITE_EVERY_SAMPLE is False)
    last_write_time = time.time()

    # Plot setup
    plt.ion()
    fig, ax = plt.subplots()
    ax.set_title("Live Light Sensor Data")
    ax.set_xlabel("Samples (most recent on right)")
    ax.set_ylabel("Sensor value")
    ax.set_ylim(*Y_LIM)

    data_buffers = [deque(maxlen=MAX_POINTS) for _ in range(4)]
    lines = []

    for label in SENSOR_LABELS:
        (ln,) = ax.plot([], [], label=label)
        lines.append(ln)

    ax.legend()
    plt.show(block=False)

    print("▶️ Running... (Ctrl+C to stop)")

    try:
        while True:
            # Read line from serial
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            if PRINT_RAW:
                print("RAW:", raw)

            sensor_values = parse_sensor_line(raw)
            if sensor_values is None:
                if PRINT_MALFORMED:
                    print(f"⚠️ Could not parse: {raw}")
                continue

            ts_full = timestamp_full_str()
            print(f"⏱ {ts_full} | {sensor_values}")

            # Day rollover handling
            new_date = current_date_str()
            if new_date != last_date:
                lock_previous_csv(current_csv)
                current_csv = csv_path_for_today()
                write_csv_header_if_needed(current_csv)
                last_date = new_date
                print(f"🗓️ New day: now writing to {current_csv}")

            # -----------------------
            # CSV writing
            # -----------------------
            should_write = WRITE_EVERY_SAMPLE or ((time.time() - last_write_time) >= OUTPUT_INTERVAL_SEC)
            if should_write:
                with open(current_csv, "a", encoding="utf-8", newline="", buffering=1) as f:
                    f.write(f"{ts_full}," + ",".join(map(str, sensor_values)) + "\n")
                    f.flush()
                last_write_time = time.time()
                if not WRITE_EVERY_SAMPLE:
                    print(f"💾 Snapshot saved: {ts_full} | {sensor_values}")

            # -----------------------
            # Live plot update (EVERY valid sample)
            # -----------------------
            for i in range(4):
                data_buffers[i].append(sensor_values[i])

            n = len(data_buffers[0])
            xs = list(range(-n + 1, 1))  # most recent at 0

            for i in range(4):
                ys = list(data_buffers[i])
                lines[i].set_data(xs, ys)

            ax.set_xlim(-MAX_POINTS + 1, 0)

            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            plt.pause(PLOT_PAUSE_SEC)

    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
    finally:
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()