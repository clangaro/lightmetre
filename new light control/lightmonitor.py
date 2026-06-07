import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Path to the folder with light data
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"

# Load all transitions
def load_transitions():
    files = [f for f in os.listdir(DATA_DIR) if "light_transitions" in f]
    all_transitions = pd.DataFrame()
    for f in files:
        df = pd.read_csv(os.path.join(DATA_DIR, f))
        all_transitions = pd.concat([all_transitions, df], ignore_index=True)
    all_transitions['timestamp'] = pd.to_datetime(all_transitions['timestamp'])
    return all_transitions

# Streamlit UI
st.title("🧠 Light Monitoring Dashboard")
transitions = load_transitions()

sensor_options = transitions['sensor'].unique()
sensor_filter = st.multiselect("Select sensors", sensor_options, default=list(sensor_options))
event_filter = st.multiselect("Select events", ["ON", "OFF"], default=["ON", "OFF"])
date_filter = st.date_input("Date range", [])

filtered = transitions[
    (transitions['sensor'].isin(sensor_filter)) &
    (transitions['event'].isin(event_filter))
]

if date_filter:
    filtered = filtered[filtered['timestamp'].dt.date.isin(date_filter)]

st.write("### Detected Transitions", filtered)

# Plot transitions over time
fig, ax = plt.subplots()
for sensor in sensor_filter:
    sensor_data = filtered[filtered['sensor'] == sensor]
    ax.scatter(sensor_data['timestamp'], [sensor] * len(sensor_data), label=sensor)

ax.set_title("Light ON/OFF Transitions Over Time")
ax.set_ylabel("Sensor")
ax.set_xlabel("Timestamp")
plt.xticks(rotation=45)
st.pyplot(fig)
