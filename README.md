# ParkOS — Frontend

## Files
| File            | Purpose                          | Port  |
|-----------------|----------------------------------|-------|
| `display.py`    | Public live slot display         | 8501  |
| `admin.py`      | Admin floor management           | 8502  |
| `user.py`       | User park/exit/search/logs       | 8503  |
| `config.py`     | Shared config & CSS              | —     |
| `requirements.txt` | Python dependencies           | —     |

## Setup
```bash
pip install -r requirements.txt
```

## Run all 3 portals (open 3 terminals)
```bash
# Terminal 1 — Public Display
streamlit run display.py --server.port 8501

# Terminal 2 — Admin Portal (password: admin123)
streamlit run admin.py --server.port 8502

# Terminal 3 — User Portal
streamlit run user.py --server.port 8503
```

## Access
- Display : http://localhost:8501
- Admin   : http://localhost:8502
- User    : http://localhost:8503

## Notes
- Make sure FastAPI backend is running on port 8000 first
- Admin password is set in admin.py (default: admin123)
- Sensor fine check is in the "Exit" tab of the User portal
