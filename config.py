API_URL = "http://localhost:8000"

# Shared CSS injected into every portal
COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}

/* Hide default streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Dark industrial base */
.stApp {
    background-color: #0d0f14;
    color: #e8e6e0;
}

/* Metric cards */
.metric-card {
    background: #161a22;
    border: 1px solid #2a2f3d;
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.metric-card .label {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6b7280;
    font-family: 'DM Mono', monospace;
}
.metric-card .value {
    font-size: 28px;
    font-weight: 800;
    color: #f0ede8;
    margin-top: 4px;
    line-height: 1;
}

/* Slot grid */
.slot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
    gap: 8px;
    margin: 12px 0 24px 0;
}
.slot {
    aspect-ratio: 1;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    cursor: default;
    transition: transform 0.15s;
}
.slot:hover { transform: scale(1.05); }
.slot.available {
    background: #0d2b1a;
    border: 1px solid #1a5c35;
    color: #34d473;
}
.slot.occupied {
    background: #2a0f0f;
    border: 1px solid #5c1a1a;
    color: #e05252;
}
.slot.selected {
    background: #1a2a4a;
    border: 2px solid #4a90e2;
    color: #7ab8f5;
}
.slot .slot-icon { font-size: 18px; line-height: 1; }
.slot .slot-id { font-size: 10px; margin-top: 2px; opacity: 0.8; }

/* Floor section */
.floor-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0 6px 0;
    border-bottom: 1px solid #2a2f3d;
    margin-bottom: 14px;
}
.floor-badge {
    background: #1e2330;
    border: 1px solid #3a4060;
    border-radius: 4px;
    padding: 4px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #9ba8cc;
    letter-spacing: 1px;
}
.vehicle-tag {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6b7280;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 3px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    font-weight: 500;
}
.badge-green  { background: #0d2b1a; color: #34d473; border: 1px solid #1a5c35; }
.badge-red    { background: #2a0f0f; color: #e05252; border: 1px solid #5c1a1a; }
.badge-blue   { background: #0f1e36; color: #7ab8f5; border: 1px solid #1a3a6b; }
.badge-amber  { background: #2a1f0a; color: #f5a623; border: 1px solid #5c3d10; }
.badge-purple { background: #1a0f36; color: #b07ef5; border: 1px solid #3a1a6b; }

/* Log table */
.log-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
}
.log-table th {
    background: #161a22;
    color: #6b7280;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 10px;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #2a2f3d;
}
.log-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #1a1f2a;
    color: #c8c4bc;
}
.log-table tr:hover td { background: #161a22; }

/* Page title style */
.page-title {
    font-size: 32px;
    font-weight: 800;
    color: #f0ede8;
    letter-spacing: -1px;
    line-height: 1;
    margin-bottom: 4px;
}
.page-subtitle {
    font-size: 12px;
    color: #6b7280;
    letter-spacing: 3px;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
    margin-bottom: 28px;
}

/* Alert boxes */
.alert {
    padding: 14px 18px;
    border-radius: 5px;
    margin: 12px 0;
    font-size: 13px;
}
.alert-success { background:#0d2b1a; border-left:3px solid #34d473; color:#34d473; }
.alert-error   { background:#2a0f0f; border-left:3px solid #e05252; color:#e05252; }
.alert-info    { background:#0f1e36; border-left:3px solid #4a90e2; color:#7ab8f5; }
.alert-warning { background:#2a1f0a; border-left:3px solid #f5a623; color:#f5a623; }

/* Fine alert */
.fine-alert {
    background: #2a0f0f;
    border: 1px solid #e05252;
    border-radius: 6px;
    padding: 20px 24px;
    text-align: center;
    margin: 16px 0;
}
.fine-amount {
    font-size: 48px;
    font-weight: 800;
    color: #e05252;
    font-family: 'DM Mono', monospace;
    line-height: 1;
}

/* Streamlit widget overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select,
div[data-testid="stNumberInput"] input {
    background-color: #161a22 !important;
    border: 1px solid #2a2f3d !important;
    color: #e8e6e0 !important;
    border-radius: 4px !important;
}
div[data-testid="stButton"] button {
    background-color: #1e2330 !important;
    border: 1px solid #3a4060 !important;
    color: #c8c4bc !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 1px !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
}
div[data-testid="stButton"] button:hover {
    background-color: #2a3048 !important;
    border-color: #4a90e2 !important;
    color: #7ab8f5 !important;
}
div[data-testid="stTabs"] button {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: #6b7280 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f0ede8 !important;
}
div[data-testid="stForm"] {
    background: #161a22 !important;
    border: 1px solid #2a2f3d !important;
    border-radius: 6px !important;
    padding: 20px !important;
}
label, .stSelectbox label, .stTextInput label {
    color: #9ba8cc !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-family: 'DM Mono', monospace !important;
}
</style>
"""

VEHICLE_ICONS = {
    "2-Wheeler": "🏍️",
    "4-Wheeler": "🚗",
    "6-Seater":  "🚐"
}
