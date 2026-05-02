"""
user.py — User Portal
Run: streamlit run frontend/user.py --server.port 8503
Handles: park, exit, slot selection, search, history, sensor fine.
"""

import streamlit as st
import requests
from datetime import datetime
from config import API_URL, COMMON_CSS, VEHICLE_ICONS

st.set_page_config(
    page_title="ParkOS — User",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🚗 User Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Park · Exit · Search · History</div>', unsafe_allow_html=True)
st.markdown('<hr style="border:none; border-top:1px solid #2a2f3d; margin:0 0 20px 0;">', unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
for key in ["available_slots", "chosen_slot", "park_vehicle_no", "park_vehicle_type", "park_success"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🅿️  Park Vehicle", "🚪  Exit", "🔍  Search", "📋  History & Logs"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PARK VEHICLE
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div style="font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin-bottom:16px;">Enter Vehicle Details</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1])

    with left_col:
        with st.form("park_form"):
            vehicle_no = st.text_input(
                "Vehicle Number",
                placeholder="e.g. MH12AB1234",
                help="Enter your vehicle registration number"
            )
            vehicle_type = st.selectbox(
                "Vehicle Type",
                ["2-Wheeler", "4-Wheeler", "6-Seater"]
            )
            find_btn = st.form_submit_button("🔎  Find Available Slots", use_container_width=True)

        if find_btn:
            if not vehicle_no.strip():
                st.markdown('<div class="alert alert-error">❌ Please enter a vehicle number.</div>', unsafe_allow_html=True)
            else:
                try:
                    res = requests.get(
                        f"{API_URL}/slots",
                        params={"vehicle_type": vehicle_type},
                        timeout=5
                    )
                    floors = res.json()
                    available = []
                    for f in floors:
                        for s in f.get("slots", []):
                            if not s.get("is_occupied"):
                                available.append({
                                    "slot_id":    s["slot_id"],
                                    "floor_no":   f["floor_no"],
                                    "vehicle_type": f["vehicle_type"]
                                })
                    st.session_state.available_slots   = available
                    st.session_state.park_vehicle_no   = vehicle_no.strip().upper()
                    st.session_state.park_vehicle_type = vehicle_type
                    st.session_state.park_success      = None
                    st.session_state.chosen_slot       = None
                except Exception as e:
                    st.markdown(f'<div class="alert alert-warning">⚠️ Backend unreachable: {e}</div>', unsafe_allow_html=True)

    with right_col:
        if st.session_state.available_slots is not None:
            avail = st.session_state.available_slots
            v_no  = st.session_state.park_vehicle_no
            v_type = st.session_state.park_vehicle_type

            if avail:
                st.markdown(f"""
                    <div class="alert alert-info">
                        {len(avail)} slots available for <strong>{v_type}</strong> — Vehicle: <code style="font-family:'DM Mono',monospace;">{v_no}</code>
                    </div>
                """, unsafe_allow_html=True)

                slot_ids = [s["slot_id"] for s in avail]

                # Visual slot picker
                st.markdown('<div style="font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin:12px 0 8px 0;">Select a Slot</div>', unsafe_allow_html=True)

                # Show slots as a clickable grid (using radio in a grid-like layout)
                chosen = st.radio(
                    "Available slots",
                    slot_ids,
                    horizontal=True,
                    label_visibility="collapsed"
                )
                st.session_state.chosen_slot = chosen

                # Show slot info
                slot_info = next((s for s in avail if s["slot_id"] == chosen), None)
                if slot_info:
                    st.markdown(f"""
                        <div style="background:#0f1e36; border:1px solid #1a3a6b; border-radius:5px; padding:12px 16px; margin:10px 0;">
                            <span class="badge badge-blue">Selected</span>
                            <span style="font-family:'DM Mono',monospace; font-size:14px; color:#7ab8f5; margin-left:10px;">{chosen}</span>
                            <span style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; margin-left:10px;">Floor {slot_info['floor_no']}</span>
                        </div>
                    """, unsafe_allow_html=True)

                if st.button("✅  Confirm Parking", use_container_width=True):
                    try:
                        res = requests.post(f"{API_URL}/user/park", json={
                            "vehicle_no":   v_no,
                            "vehicle_type": v_type,
                            "slot_id":      chosen
                        }, timeout=5)
                        if res.status_code == 200:
                            st.session_state.park_success    = True
                            st.session_state.available_slots = None
                        else:
                            st.markdown(f'<div class="alert alert-error">❌ {res.json().get("detail", "Parking failed")}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="alert alert-warning">⚠️ Backend error: {e}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="alert alert-error">
                        ❌ No available slots for <strong>{v_type}</strong>. 
                        Try a different vehicle type or check later.
                    </div>
                """, unsafe_allow_html=True)

        if st.session_state.park_success:
            v_no   = st.session_state.park_vehicle_no
            slot   = st.session_state.chosen_slot
            icon   = VEHICLE_ICONS.get(st.session_state.park_vehicle_type, "🚗")
            st.markdown(f"""
                <div style="background:#0d2b1a; border:1px solid #1a5c35; border-radius:6px; padding:24px 20px; text-align:center; margin-top:16px;">
                    <div style="font-size:32px;">{icon}</div>
                    <div style="font-size:20px; font-weight:700; color:#34d473; margin:8px 0 4px 0;">Parking Confirmed!</div>
                    <div style="font-family:'DM Mono',monospace; font-size:13px; color:#9ba8cc;">
                        {v_no} &nbsp;→&nbsp; Slot <strong style="color:#34d473;">{slot}</strong>
                    </div>
                    <div style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; margin-top:6px;">
                        {datetime.now().strftime('%d %b %Y, %H:%M:%S')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Park Another Vehicle"):
                st.session_state.park_success = None
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EXIT
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div style="font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin-bottom:16px;">Vehicle Exit</div>', unsafe_allow_html=True)

    left_col2, right_col2 = st.columns([1, 1])

    with left_col2:
        with st.form("exit_form"):
            exit_vehicle_no = st.text_input(
                "Vehicle Number",
                placeholder="e.g. MH12AB1234"
            )
            exit_btn = st.form_submit_button("🚪  Mark as Exited", use_container_width=True)

        if exit_btn:
            if not exit_vehicle_no.strip():
                st.markdown('<div class="alert alert-error">❌ Please enter a vehicle number.</div>', unsafe_allow_html=True)
            else:
                try:
                    res = requests.post(f"{API_URL}/user/exit", json={
                        "vehicle_no": exit_vehicle_no.strip().upper()
                    }, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        duration = data.get("duration_minutes", "—")
                        slot_id  = data.get("slot_id", "—")
                        st.markdown(f"""
                            <div style="background:#0d2b1a; border:1px solid #1a5c35; border-radius:6px; padding:20px; margin-top:12px; text-align:center;">
                                <div style="font-size:28px;">🚪</div>
                                <div style="font-size:18px; font-weight:700; color:#34d473; margin:6px 0;">Vehicle Exited</div>
                                <div style="font-family:'DM Mono',monospace; font-size:12px; color:#9ba8cc;">
                                    {exit_vehicle_no.upper()} &nbsp;|&nbsp; Slot {slot_id}
                                </div>
                                <div style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; margin-top:4px;">
                                    Duration: {duration} mins
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        detail = res.json().get("detail", "Vehicle not found or already exited")
                        st.markdown(f'<div class="alert alert-error">❌ {detail}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="alert alert-warning">⚠️ Backend error: {e}</div>', unsafe_allow_html=True)

    with right_col2:
        st.markdown("""
            <div style="background:#161a22; border:1px solid #2a2f3d; border-radius:6px; padding:20px 18px;">
                <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; margin-bottom:12px;">Exit Instructions</div>
                <ol style="font-size:13px; color:#9ba8cc; line-height:2; padding-left:18px;">
                    <li>Enter your vehicle registration number</li>
                    <li>Click "Mark as Exited"</li>
                    <li>Your slot will be freed immediately</li>
                    <li>Exit log will be recorded automatically</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)

        # Sensor fine check section
        st.markdown("")
        st.markdown("""
            <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#e05252; text-transform:uppercase; margin-bottom:10px;">
                🚨 Sensor Fine Check
            </div>
        """, unsafe_allow_html=True)

        with st.form("sensor_form"):
            sensor_veh  = st.text_input("Vehicle Number", placeholder="MH12AB1234", key="sensor_veh_input")
            actual_slot = st.text_input("Actual Slot (detected by sensor)", placeholder="e.g. F1-03")
            verify_btn  = st.form_submit_button("⚡ Verify Slot", use_container_width=True)

        if verify_btn:
            if not sensor_veh.strip() or not actual_slot.strip():
                st.markdown('<div class="alert alert-error">❌ Fill both fields.</div>', unsafe_allow_html=True)
            else:
                try:
                    res = requests.post(f"{API_URL}/sensor/verify", json={
                        "vehicle_no":  sensor_veh.strip().upper(),
                        "actual_slot": actual_slot.strip()
                    }, timeout=5)
                    result = res.json()
                    if result.get("fine"):
                        st.markdown(f"""
                            <div class="fine-alert">
                                <div style="font-size:14px; color:#e05252; letter-spacing:2px; text-transform:uppercase; font-family:'DM Mono',monospace; margin-bottom:8px;">WRONG SLOT — FINE ISSUED</div>
                                <div class="fine-amount">₹100</div>
                                <div style="font-family:'DM Mono',monospace; font-size:11px; color:#9b5252; margin-top:8px;">
                                    {sensor_veh.upper()} parked at {actual_slot} instead of assigned slot {result.get("assigned_slot","—")}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="alert alert-success">
                                ✅ Correct slot! {sensor_veh.upper()} is parked at assigned slot {actual_slot}.
                            </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="alert alert-warning">⚠️ Backend error: {e}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div style="font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin-bottom:16px;">Search by Vehicle Number</div>', unsafe_allow_html=True)

    search_col, _ = st.columns([2, 1])
    with search_col:
        with st.form("search_form"):
            search_no  = st.text_input("Vehicle Number", placeholder="e.g. MH12AB1234")
            search_btn = st.form_submit_button("🔍  Search", use_container_width=True)

    if search_btn:
        if not search_no.strip():
            st.markdown('<div class="alert alert-error">❌ Enter a vehicle number to search.</div>', unsafe_allow_html=True)
        else:
            try:
                res = requests.get(
                    f"{API_URL}/user/search",
                    params={"veh": search_no.strip().upper()},
                    timeout=5
                )
                if res.status_code == 200:
                    data = res.json()
                    v     = data.get("vehicle", {})
                    logs  = data.get("logs", [])
                    fines = data.get("fines", [])

                    if v:
                        status_css = "badge-green" if not v.get("is_parked") else "badge-blue"
                        status_txt = "CURRENTLY PARKED" if v.get("is_parked") else "NOT IN PARKING"
                        icon = VEHICLE_ICONS.get(v.get("vehicle_type", ""), "🚗")

                        st.markdown(f"""
                            <div style="background:#161a22; border:1px solid #2a2f3d; border-radius:6px; padding:20px; margin-bottom:16px;">
                                <div style="display:flex; align-items:center; gap:14px;">
                                    <span style="font-size:28px;">{icon}</span>
                                    <div>
                                        <div style="font-size:20px; font-weight:700; color:#f0ede8; font-family:'DM Mono',monospace;">{v.get("vehicle_no","—")}</div>
                                        <div style="font-size:12px; color:#6b7280; margin-top:2px;">{v.get("vehicle_type","—")}</div>
                                    </div>
                                    <span class="badge {status_css}" style="margin-left:auto;">{status_txt}</span>
                                </div>
                                <div style="display:flex; gap:24px; margin-top:14px; padding-top:12px; border-top:1px solid #2a2f3d;">
                                    <div>
                                        <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase;">Assigned Slot</div>
                                        <div style="font-family:'DM Mono',monospace; font-size:14px; color:#7ab8f5; margin-top:2px;">{v.get("slot_id","—")}</div>
                                    </div>
                                    <div>
                                        <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase;">Entry Time</div>
                                        <div style="font-family:'DM Mono',monospace; font-size:13px; color:#9ba8cc; margin-top:2px;">{v.get("entry_time","—")}</div>
                                    </div>
                                    <div>
                                        <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase;">Total Fines</div>
                                        <div style="font-family:'DM Mono',monospace; font-size:14px; color:{'#e05252' if fines else '#34d473'}; margin-top:2px;">₹{len(fines)*100}</div>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Log history for this vehicle
                    if logs:
                        st.markdown('<div style="font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin:14px 0 8px 0;">Activity Log</div>', unsafe_allow_html=True)
                        rows = ""
                        for log in logs:
                            action = log.get("action", "—")
                            badge_css = "badge-green" if action == "PARK" else "badge-amber"
                            rows += f"""
                                <tr>
                                    <td><span class="badge {badge_css}">{action}</span></td>
                                    <td style="font-family:'DM Mono',monospace;">{log.get("slot_id","—")}</td>
                                    <td>Floor {log.get("floor_no","—")}</td>
                                    <td style="font-family:'DM Mono',monospace;">{log.get("timestamp","—")}</td>
                                </tr>
                            """
                        st.markdown(f"""
                            <table class="log-table">
                                <thead>
                                    <tr><th>Action</th><th>Slot</th><th>Floor</th><th>Time</th></tr>
                                </thead>
                                <tbody>{rows}</tbody>
                            </table>
                        """, unsafe_allow_html=True)

                    # Fines
                    if fines:
                        st.markdown('<div style="font-size:10px; letter-spacing:2px; color:#e05252; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin:14px 0 8px 0;">⚠️ Fines Issued</div>', unsafe_allow_html=True)
                        fine_rows = ""
                        for fine in fines:
                            fine_rows += f"""
                                <tr>
                                    <td style="font-family:'DM Mono',monospace; color:#e05252;">₹{fine.get("amount","100")}</td>
                                    <td>{fine.get("reason","Wrong slot")}</td>
                                    <td style="font-family:'DM Mono',monospace;">{fine.get("timestamp","—")}</td>
                                </tr>
                            """
                        st.markdown(f"""
                            <table class="log-table">
                                <thead>
                                    <tr><th>Amount</th><th>Reason</th><th>Time</th></tr>
                                </thead>
                                <tbody>{fine_rows}</tbody>
                            </table>
                        """, unsafe_allow_html=True)

                    if not v:
                        st.markdown(f'<div class="alert alert-info">No vehicle found with number <code style="font-family:\'DM Mono\',monospace;">{search_no.upper()}</code></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert alert-error">❌ Vehicle not found.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="alert alert-warning">⚠️ Backend unreachable: {e}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — HISTORY & LOGS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div style="font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin-bottom:16px;">Full Parking Log</div>', unsafe_allow_html=True)

    # Filters
    fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
    with fcol1:
        action_filter = st.selectbox("Filter by Action", ["All", "PARK", "EXIT"], key="log_action")
    with fcol2:
        veh_filter = st.text_input("Filter by Vehicle No.", placeholder="e.g. MH12", key="log_veh")
    with fcol3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh_logs = st.button("↻ Refresh", use_container_width=True)

    try:
        log_res  = requests.get(f"{API_URL}/logs", timeout=5)
        fine_res = requests.get(f"{API_URL}/fines", timeout=5)
        all_logs  = log_res.json()  if log_res.status_code  == 200 else []
        all_fines = fine_res.json() if fine_res.status_code == 200 else []
        logs_ok = True
    except Exception:
        all_logs  = []
        all_fines = []
        logs_ok   = False

    # Apply filters
    filtered = all_logs
    if action_filter != "All":
        filtered = [l for l in filtered if l.get("action") == action_filter]
    if veh_filter.strip():
        filtered = [l for l in filtered if veh_filter.upper() in l.get("vehicle_no", "").upper()]

    # Log table
    if filtered:
        rows = ""
        for log in filtered:
            action    = log.get("action", "—")
            badge_css = "badge-green" if action == "PARK" else "badge-amber"
            veh_no    = log.get("vehicle_no", "—")
            slot_id   = log.get("slot_id", "—")
            floor_no  = log.get("floor_no", "—")
            timestamp = log.get("timestamp", "—")
            rows += f"""
                <tr>
                    <td><span class="badge {badge_css}">{action}</span></td>
                    <td style="font-family:'DM Mono',monospace;">{veh_no}</td>
                    <td style="font-family:'DM Mono',monospace;">{slot_id}</td>
                    <td>Floor {floor_no}</td>
                    <td style="font-family:'DM Mono',monospace; color:#6b7280;">{timestamp}</td>
                </tr>
            """
        st.markdown(f"""
            <table class="log-table">
                <thead>
                    <tr><th>Action</th><th>Vehicle No.</th><th>Slot</th><th>Floor</th><th>Timestamp</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="font-family:'DM Mono',monospace; font-size:11px; color:#6b7280; margin-top:8px; text-align:right;">
                {len(filtered)} record(s) shown
            </div>
        """, unsafe_allow_html=True)
    elif logs_ok:
        st.markdown('<div class="alert alert-info">No logs found matching the current filters.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-warning">⚠️ Could not fetch logs. Is the backend running?</div>', unsafe_allow_html=True)

    # Fines summary
    if all_fines:
        st.markdown("")
        st.markdown('<div style="font-size:10px; letter-spacing:2px; color:#e05252; text-transform:uppercase; font-family:\'DM Mono\',monospace; margin-bottom:10px;">⚠️ All Fines</div>', unsafe_allow_html=True)

        total_fine_amount = sum(f.get("amount", 100) for f in all_fines)

        fcol_a, fcol_b = st.columns([1, 3])
        with fcol_a:
            st.markdown(f"""
                <div class="metric-card" style="border-left:3px solid #e05252;">
                    <div class="label">Total Fines Collected</div>
                    <div class="value" style="color:#e05252;">₹{total_fine_amount}</div>
                </div>
            """, unsafe_allow_html=True)
        with fcol_b:
            fine_rows = ""
            for fine in all_fines:
                fine_rows += f"""
                    <tr>
                        <td style="font-family:'DM Mono',monospace;">{fine.get("vehicle_no","—")}</td>
                        <td style="font-family:'DM Mono',monospace; color:#e05252;">₹{fine.get("amount",100)}</td>
                        <td>{fine.get("reason","Wrong slot")}</td>
                        <td style="font-family:'DM Mono',monospace; color:#6b7280;">{fine.get("timestamp","—")}</td>
                    </tr>
                """
            st.markdown(f"""
                <table class="log-table">
                    <thead><tr><th>Vehicle No.</th><th>Amount</th><th>Reason</th><th>Time</th></tr></thead>
                    <tbody>{fine_rows}</tbody>
                </table>
            """, unsafe_allow_html=True)
