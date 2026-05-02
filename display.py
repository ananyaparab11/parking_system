"""
display.py — Public Display Portal
Run: streamlit run frontend/display.py --server.port 8501
Shows live availability of parking slots floor-wise.
No login required.
"""

import streamlit as st
import requests
from datetime import datetime
from config import API_URL, COMMON_CSS, VEHICLE_ICONS

st.set_page_config(
    page_title="ParkOS — Live View",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_time = st.columns([3, 1])
with col_title:
    st.markdown('<div class="page-title">🅿️ ParkOS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Live Slot Display</div>', unsafe_allow_html=True)
with col_time:
    st.markdown(f"""
        <div style="text-align:right; padding-top:8px;">
            <div style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; letter-spacing:2px; text-transform:uppercase;">Last updated</div>
            <div style="font-family:'DM Mono',monospace; font-size:14px; color:#9ba8cc;">{datetime.now().strftime('%H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<hr style="border:none; border-top:1px solid #2a2f3d; margin:0 0 20px 0;">', unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
with filter_col1:
    vehicle_filter = st.selectbox(
        "Vehicle Type",
        ["All", "2-Wheeler", "4-Wheeler", "6-Seater"]
    )
with filter_col2:
    floor_filter = st.selectbox("Floor", ["All Floors"] + [f"Floor {i}" for i in range(1, 11)])
with filter_col3:
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)

if auto_refresh:
    st.markdown("""
        <script>
        setTimeout(function(){ window.location.reload(); }, 30000);
        </script>
    """, unsafe_allow_html=True)

# ── Fetch data ────────────────────────────────────────────────────────────────
try:
    response = requests.get(f"{API_URL}/slots", timeout=5)
    floors_data = response.json()
    backend_ok = True
except Exception:
    backend_ok = False
    floors_data = []

# ── Summary stats ─────────────────────────────────────────────────────────────
if backend_ok and floors_data:
    total_slots = sum(len(f.get("slots", [])) for f in floors_data)
    occupied    = sum(1 for f in floors_data for s in f.get("slots", []) if s.get("is_occupied"))
    available   = total_slots - occupied
    pct_full    = int((occupied / total_slots * 100)) if total_slots > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="label">Total Slots</div>
                <div class="value">{total_slots}</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid #34d473;">
                <div class="label">Available</div>
                <div class="value" style="color:#34d473;">{available}</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid #e05252;">
                <div class="label">Occupied</div>
                <div class="value" style="color:#e05252;">{occupied}</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        bar_color = "#34d473" if pct_full < 70 else "#f5a623" if pct_full < 90 else "#e05252"
        st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid {bar_color};">
                <div class="label">Occupancy</div>
                <div class="value" style="color:{bar_color};">{pct_full}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ── Floor-wise slot grid ───────────────────────────────────────────────────
    for floor in floors_data:
        f_no   = floor.get("floor_no", "?")
        v_type = floor.get("vehicle_type", "")
        slots  = floor.get("slots", [])

        # Apply filters
        if vehicle_filter != "All" and v_type != vehicle_filter:
            continue
        if floor_filter != "All Floors" and f"Floor {f_no}" != floor_filter:
            continue

        floor_avail = sum(1 for s in slots if not s.get("is_occupied"))
        icon = VEHICLE_ICONS.get(v_type, "🚗")

        st.markdown(f"""
            <div class="floor-header">
                <span class="floor-badge">FLOOR {f_no}</span>
                <span style="font-size:18px;">{icon}</span>
                <span class="vehicle-tag">{v_type}</span>
                <span style="margin-left:auto; font-family:'DM Mono',monospace; font-size:11px; color:#6b7280;">
                    {floor_avail}/{len(slots)} available
                    &nbsp;•&nbsp; {floor.get("sq_ft", "—")} sq ft
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Build slot grid HTML
        slot_html = '<div class="slot-grid">'
        for slot in slots:
            sid    = slot.get("slot_id", "??")
            occ    = slot.get("is_occupied", False)
            css    = "occupied" if occ else "available"
            dot    = "🔴" if occ else "🟢"
            veh_no = slot.get("vehicle_no", "")
            title  = f'title="{veh_no}"' if veh_no else ""
            slot_html += f'''
                <div class="slot {css}" {title}>
                    <span class="slot-icon">{dot}</span>
                    <span class="slot-id">{sid}</span>
                </div>
            '''
        slot_html += "</div>"
        st.markdown(slot_html, unsafe_allow_html=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="display:flex; gap:20px; margin-top:8px; padding:12px 0; border-top:1px solid #2a2f3d;">
            <span class="badge badge-green">🟢 Available</span>
            <span class="badge badge-red">🔴 Occupied</span>
            <span style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; margin-left:auto;">
                Hover over slot to see vehicle number
            </span>
        </div>
    """, unsafe_allow_html=True)

elif not backend_ok:
    st.markdown("""
        <div class="alert alert-warning">
            ⚠️ Backend not reachable. Start the FastAPI server:
            <code style="margin-left:8px; font-family:'DM Mono',monospace;">uvicorn backend.main:app --reload</code>
        </div>
    """, unsafe_allow_html=True)

    # Demo mode with mock data
    st.markdown('<div class="page-subtitle" style="margin-top:20px;">Demo Mode — Sample Layout</div>', unsafe_allow_html=True)

    demo_floors = [
        {"floor_no": 1, "vehicle_type": "2-Wheeler", "sq_ft": 2400,
         "slots": [{"slot_id": f"1-{i:02d}", "is_occupied": i % 3 == 0} for i in range(1, 21)]},
        {"floor_no": 2, "vehicle_type": "4-Wheeler", "sq_ft": 4800,
         "slots": [{"slot_id": f"2-{i:02d}", "is_occupied": i % 2 == 0} for i in range(1, 16)]},
        {"floor_no": 3, "vehicle_type": "6-Seater", "sq_ft": 3200,
         "slots": [{"slot_id": f"3-{i:02d}", "is_occupied": i % 4 == 0} for i in range(1, 11)]},
    ]

    for floor in demo_floors:
        f_no   = floor["floor_no"]
        v_type = floor["vehicle_type"]
        slots  = floor["slots"]
        icon   = VEHICLE_ICONS.get(v_type, "🚗")
        avail  = sum(1 for s in slots if not s["is_occupied"])

        st.markdown(f"""
            <div class="floor-header">
                <span class="floor-badge">FLOOR {f_no}</span>
                <span style="font-size:18px;">{icon}</span>
                <span class="vehicle-tag">{v_type}</span>
                <span style="margin-left:auto; font-family:'DM Mono',monospace; font-size:11px; color:#6b7280;">
                    {avail}/{len(slots)} available &nbsp;•&nbsp; {floor["sq_ft"]} sq ft
                </span>
            </div>
        """, unsafe_allow_html=True)

        slot_html = '<div class="slot-grid">'
        for slot in slots:
            css = "occupied" if slot["is_occupied"] else "available"
            dot = "🔴" if slot["is_occupied"] else "🟢"
            slot_html += f'''
                <div class="slot {css}">
                    <span class="slot-icon">{dot}</span>
                    <span class="slot-id">{slot["slot_id"]}</span>
                </div>
            '''
        slot_html += "</div>"
        st.markdown(slot_html, unsafe_allow_html=True)

else:
    st.markdown('<div class="alert alert-info">No floor data found. Add floors via the Admin Portal.</div>', unsafe_allow_html=True)
