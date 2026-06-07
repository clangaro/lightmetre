import serial
from datetime import datetime, time as dtime
import os
import time
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
from collections import deque

# --- CONFIG ---
BAUD_RATE = 9600
SERIAL_PORT = "COM21"
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"
OUTPUT_INTERVAL = 600  # 10 minutes

# Define thresholds for both phases
TREATMENT_THRESHOLDS = [20, 20, 20, 20]       # Placeholder: lower values for dimmer light
BACKGROUND_THRESHOLDS = [500, 500, 500, 500]     # Standard
""" 
EMAIL_ADDRESS = "labkriegsfeld@gmail.com"
EMAIL_PASSWORD = "mgoi bkyd dhil iwfq"
RECIPIENTS = ["carter_bower@berkeley.edu, carolinalangaro@berkeley.edu"]"""

# --- Functions ---
def get_current_phase():
    now = datetime.now().time()
    if dtime(9, 0) <= now < dtime(10, 0):
        return 'treatment'
    elif dtime(10, 0) <= now < dtime(21, 0):
        return 'background'
    else:
        return 'off'

def get_thresholds():
    phase = get_current_phase()
    if phase == 'treatment':
        return TREATMENT_THRESHOLDS
    elif phase == 'background':
        return BACKGROUND_THRESHOLDS
    return [float('inf')] * 4  # effectively disable alerts

""" def send_email(sensor_index, value, timestamp, RECIPIENTS):
   if get_current_phase() != 'background':
        return  # skip during treatment
    subject = f"Light Sensor Alert - Sensor {sensor_index + 1} Triggered"
    body = f"Sensor {sensor_index + 1} value {value} exceeded threshold {BACKGROUND_THRESHOLDS[sensor_index]} at {timestamp}."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(RECIPIENTS)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())
        print(f"📧 Email sent for Sensor {sensor_index + 1} at {timestamp}")
    except Exception as e:
        print(f"❌ Email error: {e}") """

# --- Setup ---
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print(f"✅ Connected to {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Serial error: {e}")
    exit()

last_write_time = time.time()
alert_sent = [False] * 4
current_date_str = datetime.now().strftime("%Y-%m-%d")
csv_file = os.path.join(DATA_DIR, f"{current_date_str}_light_data.csv")
file_locked = False

if not os.path.exists(csv_file):
    with open(csv_file, 'w') as f:
        f.write("timestamp,sensor4D,sensor4B,sensor4A,sensor4C\n")

# --- Live Plot ---
plt.ion()
fig, ax = plt.subplots()
plt.show(block=False)
sensor_names = ["sensor4D", "sensor4B", "sensor4A", "sensor4C"]
lines = [ax.plot([], [], label=sensor_names[i])[0]for i in range(4)]
data_deques = [deque(maxlen=100) for _ in range(4)]
timestamps = deque(maxlen=100)
ax.set_ylim(0, 1023)
ax.set_title("Live Sensor Data")
ax.set_xlabel("Time")
ax.set_ylabel("Sensor Value")
ax.legend()

try:
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) != 4:
            print(f"⚠️ Malformed line: {line}")
            continue
        try:
            sensor_values = [int(x) for x in parts]
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📡 [{timestamp}] {sensor_values}")
        except ValueError:
            print(f"⚠️ Non-integer data: {line}")
            continue

        # --- File rotation ---
        new_date_str = datetime.now().strftime("%Y-%m-%d")
        if new_date_str != current_date_str:
            if not file_locked:
                locked_path = csv_file + ".locked"
                os.rename(csv_file, locked_path)
                print(f"🔒 Locked previous CSV: {locked_path}")
                file_locked = True
            current_date_str = new_date_str
            csv_file = os.path.join(DATA_DIR, f"{current_date_str}_light_data.csv")
            with open(csv_file, 'w') as f:
                f.write("timestamp,sensor4D,sensor4B,sensor4A,sensor4C\n")
            file_locked = False

        # --- Email alert logic ---
        #thresholds = get_thresholds()
        #for i, value in enumerate(sensor_values):
        #    if value > thresholds[i] and not alert_sent[i]:
        #        send_email(i, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #        alert_sent[i] = True

        # --- Save snapshot every 10 mins ---
        if time.time() - last_write_time >= OUTPUT_INTERVAL:
            timestamp_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(csv_file, 'a') as f:
                f.write(f"{timestamp_full},{','.join(map(str, sensor_values))}\n")
            print(f"💾 Data saved at {timestamp_full}: {sensor_values}")
            last_write_time = time.time()

        # --- Live Plot Update ---
        timestamps.append(timestamp)
        for i in range(4):
            data_deques[i].append(sensor_values[i])
            lines[i].set_xdata(range(len(data_deques[i])))
            lines[i].set_ydata(data_deques[i])
        ax.relim()
        ax.autoscale_view()

        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        plt.pause(0.05)

except KeyboardInterrupt:
    print("🛑 User stopped")
except Exception as e:
    print(f"⚠️ Error: {e}")
