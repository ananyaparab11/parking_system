"""
admin.py — Admin Portal
Run: streamlit run frontend/admin.py --server.port 8502
Manage floors, capacity, vehicle types, sq ft.
Password protected.
"""

import streamlit as st
import requests
from config import API_URL, COMMON_CSS, VEHICLE_ICONS

st.set_page_config(
    page_title="ParkOS — Admin",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown('<div class="page-title">🔧 Admin Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Restricted Access</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none; border-top:1px solid #2a2f3d; margin:0 0 28px 0;">', unsafe_allow_html=True)

    col_center, _, _ = st.columns([1, 1, 1])
    with col_center:
        st.markdown("""
            <div style="background:#161a22; border:1px solid #2a2f3d; border-radius:6px; padding:28px 24px; margin-top:20px;">
                <div style="font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; margin-bottom:16px;">
                    Enter Admin Credentials
                </div>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password")
        if st.button("→ Login", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.markdown('<div class="alert alert-error">❌ Incorrect password</div>', unsafe_allow_html=True)
    st.stop()

# ── Main Admin UI ─────────────────────────────────────────────────────────────
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.markdown('<div class="page-title">🔧 Admin Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Floor & Capacity Management</div>', unsafe_allow_html=True)
with col_logout:
    if st.button("Logout", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

st.markdown('<hr style="border:none; border-top:1px solid #2a2f3d; margin:0 0 20px 0;">', unsafe_allow_html=True)

# ── Fetch floors ──────────────────────────────────────────────────────────────
try:
    floors_resp = requests.get(f"{API_URL}/admin/floors", timeout=5)
    floors_data = floors_resp.json() if floors_resp.status_code == 200 else []
    backend_ok  = True
except Exception:
    backend_ok  = False
    floors_data = []

if not backend_ok:
    st.markdown("""
        <div class="alert alert-warning">
            ⚠️ Cannot reach backend at <code>localhost:8000</code>.
            Start with: <code>uvicorn backend.main:app --reload</code>
        </div>
    """, unsafe_allow_html=True)

# ── Summary cards ─────────────────────────────────────────────────────────────
total_floors    = len(floors_data)
total_capacity  = sum(f.get("capacity", 0) for f in floors_data)
total_sqft      = sum(f.get("sq_ft", 0) for f in floors_data)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""
        <div class="metric-card" style="border-left:3px solid #4a90e2;">
            <div class="label">Total Floors</div>
            <div class="value">{total_floors}</div>
        </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
        <div class="metric-card" style="border-left:3px solid #34d473;">
            <div class="label">Total Capacity</div>
            <div class="value">{total_capacity}</div>
        </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
        <div class="metric-card" style="border-left:3px solid #f5a623;">
            <div class="label">Total Area</div>
            <div class="value">{total_sqft:,} <span style="font-size:14px; font-weight:400; color:#6b7280;">sq ft</span></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Add / Update Floor", "View All Floors", "Delete Floor"])

# ── Tab 1: Add/Update Floor ───────────────────────────────────────────────────
with tab1:
    st.markdown('<div style="margin-bottom:16px; font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace;">Floor Configuration</div>', unsafe_allow_html=True)

    existing_floor_nos = [f.get("floor_no") for f in floors_data]

    with st.form("floor_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            floor_no = st.number_input(
                "Floor Number",
                min_value=1, max_value=20, step=1, value=1,
                help="Floor number (1–20)"
            )
            vehicle_type = st.selectbox(
                "Vehicle Type",
                ["2-Wheeler", "4-Wheeler", "6-Seater"]
            )
        with col2:
            capacity = st.number_input(
                "Number of Parking Slots",
                min_value=1, max_value=200, step=1, value=20
            )
            sq_ft = st.number_input(
                "Floor Area (sq ft)",
                min_value=100, max_value=100000, step=100, value=2400
            )

        slot_prefix = st.text_input(
            "Slot ID Prefix",
            value=f"F{floor_no}",
            help="Slot IDs will be like F1-01, F1-02 …"
        )

        submitted = st.form_submit_button(
            "💾  Save Floor",
            use_container_width=True
        )

    if submitted:
        is_update = floor_no in existing_floor_nos
        payload = {
            "floor_no":     floor_no,
            "vehicle_type": vehicle_type,
            "capacity":     capacity,
            "sq_ft":        sq_ft,
            "slot_prefix":  slot_prefix
        }
        try:
            endpoint = f"{API_URL}/admin/floor"
            res = requests.post(endpoint, json=payload, timeout=5)
            if res.status_code == 200:
                action = "updated" if is_update else "created"
                st.markdown(f'<div class="alert alert-success">✅ Floor {floor_no} ({vehicle_type}) {action} with {capacity} slots.</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown(f'<div class="alert alert-error">❌ Error: {res.text}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="alert alert-warning">⚠️ Backend unreachable: {e}</div>', unsafe_allow_html=True)

    # Quick vehicle type guide
    st.markdown("")
    st.markdown("""
        <div style="background:#161a22; border:1px solid #2a2f3d; border-radius:6px; padding:16px 20px;">
            <div style="font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; margin-bottom:10px;">Vehicle Type Guide</div>
            <div style="display:flex; gap:24px;">
                <div>🏍️ <span style="font-family:'DM Mono',monospace; font-size:12px; color:#9ba8cc;">2-Wheeler</span> — Bikes & scooters</div>
                <div>🚗 <span style="font-family:'DM Mono',monospace; font-size:12px; color:#9ba8cc;">4-Wheeler</span> — Cars & SUVs</div>
                <div>🚐 <span style="font-family:'DM Mono',monospace; font-size:12px; color:#9ba8cc;">6-Seater</span> — Vans & large vehicles</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ── Tab 2: View All Floors ─────────────────────────────────────────────────────
with tab2:
    if floors_data:
        st.markdown('<div style="margin-bottom:16px; font-size:11px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; font-family:\'DM Mono\',monospace;">All Configured Floors</div>', unsafe_allow_html=True)

        # Build HTML table
        rows_html = ""
        for f in sorted(floors_data, key=lambda x: x.get("floor_no", 0)):
            f_no   = f.get("floor_no", "—")
            v_type = f.get("vehicle_type", "—")
            cap    = f.get("capacity", 0)
            sqft   = f.get("sq_ft", 0)
            icon   = VEHICLE_ICONS.get(v_type, "🚗")
            prefix = f.get("slot_prefix", f"F{f_no}")

            rows_html += f"""
                <tr>
                    <td><span class="badge badge-blue">F{f_no}</span></td>
                    <td>{icon} {v_type}</td>
                    <td style="font-family:'DM Mono',monospace;">{cap}</td>
                    <td style="font-family:'DM Mono',monospace;">{sqft:,}</td>
                    <td style="font-family:'DM Mono',monospace; color:#6b7280;">{prefix}-XX</td>
                </tr>
            """

        st.markdown(f"""
            <table class="log-table">
                <thead>
                    <tr>
                        <th>Floor</th>
                        <th>Vehicle Type</th>
                        <th>Capacity</th>
                        <th>Area (sq ft)</th>
                        <th>Slot Format</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        """, unsafe_allow_html=True)

        # Per-type breakdown
        st.markdown("")
        st.markdown('<div style="font-family:\'DM Mono\',monospace; font-size:10px; letter-spacing:2px; color:#6b7280; text-transform:uppercase; margin-bottom:10px;">Capacity by Vehicle Type</div>', unsafe_allow_html=True)

        type_totals = {}
        for f in floors_data:
            vt = f.get("vehicle_type", "Unknown")
            type_totals[vt] = type_totals.get(vt, 0) + f.get("capacity", 0)

        cols = st.columns(len(type_totals) or 1)
        for idx, (vt, total) in enumerate(type_totals.items()):
            icon = VEHICLE_ICONS.get(vt, "🚗")
            with cols[idx]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">{icon} {vt}</div>
                        <div class="value">{total} <span style="font-size:13px; font-weight:400; color:#6b7280;">slots</span></div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info">No floors configured yet. Use the "Add / Update Floor" tab.</div>', unsafe_allow_html=True)

# ── Tab 3: Delete Floor ───────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="alert alert-error">⚠️ Deleting a floor will remove all its slots and associated records.</div>', unsafe_allow_html=True)
    st.markdown("")

    if floors_data:
        floor_options = {f"Floor {f['floor_no']} — {f['vehicle_type']}": f["floor_no"] for f in floors_data}
        selected_label = st.selectbox("Select Floor to Delete", list(floor_options.keys()))
        selected_floor_no = floor_options[selected_label]

        confirm = st.checkbox(f"I confirm I want to delete Floor {selected_floor_no} and all its data")

        if st.button("🗑️  Delete Floor", disabled=not confirm):
            try:
                res = requests.delete(f"{API_URL}/admin/floor/{selected_floor_no}", timeout=5)
                if res.status_code == 200:
                    st.markdown(f'<div class="alert alert-success">✅ Floor {selected_floor_no} deleted.</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown(f'<div class="alert alert-error">❌ Delete failed: {res.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="alert alert-warning">⚠️ Backend unreachable: {e}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info">No floors to delete.</div>', unsafe_allow_html=True)
