import time
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go


# =============================
# iPaddy — Farmer Movie View
# =============================

st.set_page_config(
    page_title="iPaddy",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main {
        max-width: 480px;
        margin: auto;
    }

    h1 {
        text-align: center;
        font-size: 2.1rem !important;
        margin-bottom: 0rem;
    }

    .subtitle {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.7rem;
    }

    .timebox {
        text-align: center;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 0.3rem;
        margin-bottom: 0.5rem;
    }

    .status-card {
        padding: 0.75rem;
        border-radius: 18px;
        background: #f5f7f4;
        text-align: center;
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
    }

    .big-water {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1769aa;
    }

    .recommendation {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }

    .movie-button button {
        font-size: 1.2rem !important;
        height: 3rem;
    }

    img.ipaddy-image {
        width: 100%;
        max-height: 42vh;
        object-fit: cover;
        border-radius: 20px;
        display: block;
        margin: auto;
    }

    .small-note {
        text-align: center;
        font-size: 0.85rem;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# File names
# -----------------------------
WATER_FILE = "ACTS616ModelSignal.csv"
DAILY_WEATHER_FILE = "ModelApp_weather_daily_2026-06-15_2026-06-25.csv"
HOURLY_WEATHER_FILE = "ModelApp_weather_hourly_2026-06-15_2026-06-25.csv"

DRY_IMG = "dry.png"
NORMAL_IMG = "normal.png"
HIGH_IMG = "high.png"


# -----------------------------
# Helpers
# -----------------------------
def load_csv_required(filename):
    if not Path(filename).exists():
        st.error(f"Missing file: {filename}")
        st.stop()
    return pd.read_csv(filename)


def image_html(filename):
    path = Path(filename)
    if not path.exists():
        st.warning(f"Missing image: {filename}")
        return

    data = base64.b64encode(path.read_bytes()).decode()
    st.markdown(
        f"""
        <img class="ipaddy-image" src="data:image/png;base64,{data}">
        """,
        unsafe_allow_html=True,
    )


def classify_water(level):
    if level < 6.5:
        return {
            "image": DRY_IMG,
            "status": "Water is low",
            "recommendation": "Pump soon",
            "emoji": "🟡",
        }
    elif level < 15:
        return {
            "image": NORMAL_IMG,
            "status": "Water is good",
            "recommendation": "No action needed",
            "emoji": "🟢",
        }
    else:
        return {
            "image": HIGH_IMG,
            "status": "Water is high",
            "recommendation": "Watch overflow",
            "emoji": "🔵",
        }


def pump_status(ts):
    # Demo events from the known replay period
    if pd.Timestamp("2026-06-16 08:50") <= ts <= pd.Timestamp("2026-06-16 20:50"):
        return "Pump ON"
    if pd.Timestamp("2026-06-23 12:40") <= ts <= pd.Timestamp("2026-06-23 18:40"):
        return "Pump ON"
    return "Pump OFF"


def event_note(ts):
    if pd.Timestamp("2026-06-16 08:50") <= ts <= pd.Timestamp("2026-06-16 20:50"):
        return "Irrigation in progress"
    if pd.Timestamp("2026-06-19 15:00") <= ts <= pd.Timestamp("2026-06-21 23:59"):
        return "Rain period"
    if pd.Timestamp("2026-06-23 12:40") <= ts <= pd.Timestamp("2026-06-23 18:40"):
        return "Pump running"
    return "Field monitoring"


def get_weather_for_time(ts, daily_weather):
    date_str = ts.strftime("%Y-%m-%d")

    row = daily_weather[daily_weather["date"] == date_str]

    if row.empty:
        return {
            "label": "Weather unavailable",
            "temp": None,
            "rain": None,
            "alert": "",
        }

    row = row.iloc[0]
    temp = (row["temp_min_c"] + row["temp_max_c"]) / 2

    return {
        "label": row["app_weather_label"],
        "temp": temp,
        "rain": row["precip_mm"],
        "alert": row["alert_ko"],
    }


# -----------------------------
# Load data
# -----------------------------
water = load_csv_required(WATER_FILE)
daily_weather = load_csv_required(DAILY_WEATHER_FILE)

water["Timestamp"] = pd.to_datetime(water["Timestamp"])
water = water.sort_values("Timestamp").reset_index(drop=True)


# -----------------------------
# Session state
# -----------------------------
if "index" not in st.session_state:
    st.session_state.index = len(water) - 1

if "playing" not in st.session_state:
    st.session_state.playing = False


# -----------------------------
# Header
# -----------------------------
st.title("iPaddy")
st.markdown('<div class="subtitle">Rice Field Replay</div>', unsafe_allow_html=True)


# -----------------------------
# Current frame
# -----------------------------
current = water.iloc[st.session_state.index]
ts = current["Timestamp"]
level = float(current["WaterLevel"])

water_state = classify_water(level)
weather = get_weather_for_time(ts, daily_weather)
pump = pump_status(ts)
note = event_note(ts)


# -----------------------------
# Time
# -----------------------------
st.markdown(
    f"""
    <div class="timebox">
        {ts.strftime("%B %d")}<br>
        {ts.strftime("%I:%M %p")}
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Main field image
# -----------------------------
image_html(water_state["image"])


# -----------------------------
# Main farmer status
# -----------------------------
st.markdown(
    f"""
    <div class="status-card">
        <div class="big-water">💧 {level:.1f} cm</div>
        <div class="recommendation">
            {water_state["emoji"]} {water_state["status"]} · {water_state["recommendation"]}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Weather / pump compact cards
# -----------------------------
c1, c2 = st.columns(2)

with c1:
    if weather["temp"] is not None:
        st.metric("Weather", weather["label"], f"{weather['temp']:.1f}°C")
    else:
        st.metric("Weather", weather["label"])

with c2:
    st.metric("Pump", pump)

st.markdown(f'<div class="small-note">{note}</div>', unsafe_allow_html=True)


# -----------------------------
# Movie controls
# -----------------------------
st.markdown("---")

jump = st.selectbox(
    "Jump size",
    options=[1, 6, 18, 72, 144],
    index=1,
    format_func=lambda x: {
        1: "10 min",
        6: "1 hour",
        18: "3 hours",
        72: "12 hours",
        144: "1 day",
    }[x],
)

speed = st.selectbox(
    "Play speed",
    options=[0.25, 0.5, 1, 2, 5],
    index=2,
    format_func=lambda x: f"{x}×",
)

b1, b2, b3, b4, b5, b6 = st.columns(6)

with b1:
    if st.button("⏮", use_container_width=True):
        st.session_state.index = 0
        st.session_state.playing = False
        st.rerun()

with b2:
    if st.button("⏪", use_container_width=True):
        st.session_state.index = max(0, st.session_state.index - jump)
        st.session_state.playing = False
        st.rerun()

with b3:
    if st.button("▶", use_container_width=True):
        st.session_state.playing = True
        st.rerun()

with b4:
    if st.button("⏸", use_container_width=True):
        st.session_state.playing = False
        st.rerun()

with b5:
    if st.button("⏩", use_container_width=True):
        st.session_state.index = min(len(water) - 1, st.session_state.index + jump)
        st.session_state.playing = False
        st.rerun()

with b6:
    if st.button("⏭", use_container_width=True):
        st.session_state.index = len(water) - 1
        st.session_state.playing = False
        st.rerun()


# -----------------------------
# Time slider
# -----------------------------
st.session_state.index = st.slider(
    "Timeline",
    min_value=0,
    max_value=len(water) - 1,
    value=st.session_state.index,
)


# -----------------------------
# Optional graph
# -----------------------------
with st.expander("Water-level graph"):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=water["Timestamp"],
            y=water["WaterLevel"],
            mode="lines",
            name="Water Level",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[ts],
            y=[level],
            mode="markers",
            name="Selected Time",
            marker=dict(size=14),
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Time",
        yaxis_title="cm",
    )

    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Auto play
# -----------------------------
if st.session_state.playing:
    if st.session_state.index < len(water) - 1:
        st.session_state.index += 1
        time.sleep(0.25 / speed)
        st.rerun()
    else:
        st.session_state.playing = False
        st.rerun()
