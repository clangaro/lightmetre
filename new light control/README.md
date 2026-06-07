# Light Sensor Monitoring System

A 4-channel light sensor logger for the UCB Age Light Records project. An Arduino reads four photoresistors (one per cage / light zone), streams the values over USB, and a Python script logs them to a daily CSV and shows a live plot. A separate Streamlit app lets you browse past days and see how the recorded light intensity lines up with the scheduled treatment and background light windows.

---

## What's in this folder

| File | Purpose |
|---|---|
| `arduino/arduino.ino` | Arduino firmware. Reads 4 analog sensors and prints `val1,val2,val3,val4` over serial every 10 minutes. |
| `Graphing Light Sensor.py` | Live logger. Connects to the Arduino, prints/plots values in real time, and writes one CSV per day. |
| `light_transitions_app.py` | Streamlit dashboard. Loads a chosen day's CSV and plots each sensor with shaded treatment (09:00–10:00) and background (10:00–21:00) windows. |
| `start_light_logger.bat` | Windows one-click launcher for the logger. |

CSV files are written to `C:\Users\krieg\Desktop\UCB Age Light Records`, one per day, named `YYYY-MM-DD_light_data.csv`.

---

## Hardware setup

1. Arduino board (Uno/Nano-compatible) connected by USB.
2. Four photoresistors wired to analog inputs:
   - `sensor1` → `A3`
   - `sensor2` → `A1`
   - `sensor3` → `A4`
   - `sensor4` → `A2`
3. Each photoresistor in a voltage divider with a 10 kΩ pull-down resistor to GND, with the junction going to the analog pin and the other end of the photoresistor to 5 V.

---

## One-time software setup (Windows lab PC)

1. **Install the Arduino IDE** from https://www.arduino.cc/en/software.
2. **Install Python 3.10+** from https://www.python.org/downloads/ (tick "Add Python to PATH" during install).
3. Open a Command Prompt in this folder and install the Python packages:
   ```
   pip install pyserial matplotlib pandas streamlit
   ```
4. **Upload the firmware** to the Arduino:
   - Open `arduino/arduino.ino` in the Arduino IDE.
   - Tools → Board → select your Arduino model.
   - Tools → Port → select the Arduino's COM port (e.g. `COM21`). **Write this port number down.**
   - Click Upload (→).
5. **Tell the Python logger which port to use**:
   - Open `Graphing Light Sensor.py`.
   - On line 22 set `SERIAL_PORT = "COM21"` (or whatever port the Arduino actually appeared on).
   - Save.

---

## Daily use

### 1. Start logging (runs all day)

Double-click `start_light_logger.bat`.

A console window opens showing:
- A confirmation that the serial port connected.
- Each sample as it arrives, e.g. `⏱ 2026-06-07 09:01:22 | [482, 491, 503, 478]`.
- A live matplotlib window updating with the 4 traces.
- `💾 Snapshot saved: ...` every 10 minutes when a row is written to the CSV.

Leave this window open. To stop, click into the console window and press **Ctrl+C**, or just close the window at the end of the day.

The CSV `YYYY-MM-DD_light_data.csv` is created automatically. At midnight the script rolls over to a new file for the next day.

### 2. View a past day's data

In a Command Prompt in this folder:

```
streamlit run light_transitions_app.py
```

A browser tab opens at `http://localhost:8501` showing:
- A **date picker** with every day that has a CSV.
- One plot per sensor with the **treatment window** (09:00–10:00) shaded pink and the **background window** (10:00–21:00) shaded blue.

To stop the dashboard, go back to the Command Prompt and press Ctrl+C.

---

## Configuration

Edit these values at the top of `Graphing Light Sensor.py`:

| Variable | Meaning | Default |
|---|---|---|
| `SERIAL_PORT` | Arduino's COM port | `"COM21"` |
| `BAUD_RATE` | Must match `Serial.begin()` in firmware | `9600` |
| `DATA_DIR` | Where CSVs are written | `C:\Users\krieg\Desktop\UCB Age Light Records` |
| `WRITE_EVERY_SAMPLE` | `True` = write every sample, `False` = write a snapshot every `OUTPUT_INTERVAL_SEC` | `False` |
| `OUTPUT_INTERVAL_SEC` | Snapshot interval in seconds | `600` (10 min) |
| `Y_LIM` | Live plot y-axis range | `(0, 1023)` |

Edit these values at the top of `light_transitions_app.py`:

| Variable | Meaning | Default |
|---|---|---|
| `DATA_DIR` | Folder to read CSVs from (must match the logger) | `C:\Users\krieg\Desktop\UCB Age Light Records` |
| `TREATMENT_START` / `TREATMENT_END` | Pink shaded window | `09:00` / `10:00` |
| `BACKGROUND_START` / `BACKGROUND_END` | Blue shaded window | `10:00` / `21:00` |

If the lab's lighting schedule changes, update these four times in `light_transitions_app.py`.

---

## Troubleshooting

**`Serial error: could not open port 'COM21'`**
The COM port number changed (Windows reassigns it when you replug). Open Device Manager → Ports (COM & LPT), find the Arduino, update `SERIAL_PORT` in `Graphing Light Sensor.py`.

**Live plot never appears, but data prints to the console**
Another process owns the serial port (e.g. the Arduino IDE's Serial Monitor is open). Close it and restart the logger.

**Streamlit shows "missing ScriptRunContext! This warning can be ignored when running in bare mode"**
You launched the app with `python light_transitions_app.py`. Streamlit apps must be launched with `streamlit run light_transitions_app.py`.

**Streamlit shows "No CSV files with a YYYY-MM-DD date in the filename were found"**
`DATA_DIR` in `light_transitions_app.py` doesn't match where the logger is writing. Make sure both files have the same `DATA_DIR`.

**`⚠️ Could not parse:` messages every line**
The firmware on the Arduino isn't the one in `arduino/arduino.ino`. Re-upload it.
