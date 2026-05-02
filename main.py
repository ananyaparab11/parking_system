"""
main.py — FastAPI Backend for ParkOS
Run: uvicorn main:app --reload

All API endpoints:
  GET  /slots                  → all floors with slot availability
  GET  /slots?vehicle_type=X   → filtered by vehicle type

  GET  /admin/floors           → list all floors
  POST /admin/floor            → create or update a floor
  DELETE /admin/floor/{floor_no} → delete a floor

  POST /user/park              → park a vehicle
  POST /user/exit              → exit a vehicle
  GET  /user/search?veh=XX     → search vehicle by number

  GET  /logs                   → all parking logs
  GET  /fines                  → all fines

  POST /sensor/verify          → sensor check (wrong slot = ₹100 fine)
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

import models
import schemas
from database import engine, get_db

# ── Create all tables on startup ──────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ParkOS API",
    description="Backend for smart parking system with sensor fine detection",
    version="1.0.0"
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY ROUTES — Slot availability
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/slots", response_model=List[schemas.FloorWithSlots])
def get_all_slots(
    vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns all floors with their slots and occupancy status.
    Optionally filter by vehicle_type (2-Wheeler / 4-Wheeler / 6-Seater).
    """
    query = db.query(models.Floor)
    if vehicle_type and vehicle_type != "All":
        query = query.filter(models.Floor.vehicle_type == vehicle_type)
    floors = query.all()

    result = []
    for floor in floors:
        slots = db.query(models.Slot).filter(models.Slot.floor_id == floor.id).all()
        result.append({
            "floor_no":     floor.floor_no,
            "vehicle_type": floor.vehicle_type,
            "sq_ft":        floor.sq_ft,
            "capacity":     floor.capacity,
            "slots": [
                {
                    "slot_id":     s.slot_id,
                    "is_occupied": s.is_occupied,
                    "vehicle_no":  s.vehicle_no
                }
                for s in slots
            ]
        })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES — Floor management
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/floors", response_model=List[schemas.FloorResponse])
def get_all_floors(db: Session = Depends(get_db)):
    """Returns all configured floors."""
    return db.query(models.Floor).order_by(models.Floor.floor_no).all()


@app.post("/admin/floor")
def create_or_update_floor(
    floor_data: schemas.FloorCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new floor or update an existing one.
    Also auto-generates slots based on capacity.
    """
    # Validate vehicle type
    valid_types = ["2-Wheeler", "4-Wheeler", "6-Seater"]
    if floor_data.vehicle_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"vehicle_type must be one of {valid_types}"
        )

    prefix = floor_data.slot_prefix or f"F{floor_data.floor_no}"

    existing = db.query(models.Floor).filter(
        models.Floor.floor_no == floor_data.floor_no
    ).first()

    if existing:
        # Update floor details
        existing.vehicle_type = floor_data.vehicle_type
        existing.sq_ft        = floor_data.sq_ft
        existing.slot_prefix  = prefix

        # If capacity changed, adjust slots
        current_slots = db.query(models.Slot).filter(
            models.Slot.floor_id == existing.id
        ).count()

        if floor_data.capacity > current_slots:
            # Add new slots
            for i in range(current_slots + 1, floor_data.capacity + 1):
                new_slot = models.Slot(
                    slot_id  = f"{prefix}-{i:02d}",
                    floor_id = existing.id
                )
                db.add(new_slot)
        elif floor_data.capacity < current_slots:
            # Remove excess unoccupied slots from the end
            all_slots = db.query(models.Slot).filter(
                models.Slot.floor_id == existing.id,
                models.Slot.is_occupied == False
            ).order_by(models.Slot.id.desc()).all()

            to_remove = current_slots - floor_data.capacity
            for slot in all_slots[:to_remove]:
                db.delete(slot)

        existing.capacity = floor_data.capacity
        db.commit()
        db.refresh(existing)
        return {"message": f"Floor {floor_data.floor_no} updated", "floor_no": floor_data.floor_no}

    else:
        # Create new floor
        new_floor = models.Floor(
            floor_no     = floor_data.floor_no,
            vehicle_type = floor_data.vehicle_type,
            capacity     = floor_data.capacity,
            sq_ft        = floor_data.sq_ft,
            slot_prefix  = prefix
        )
        db.add(new_floor)
        db.flush()  # get the new floor id

        # Auto-generate slots
        for i in range(1, floor_data.capacity + 1):
            slot = models.Slot(
                slot_id  = f"{prefix}-{i:02d}",
                floor_id = new_floor.id
            )
            db.add(slot)

        db.commit()
        return {"message": f"Floor {floor_data.floor_no} created with {floor_data.capacity} slots"}


@app.delete("/admin/floor/{floor_no}")
def delete_floor(floor_no: int, db: Session = Depends(get_db)):
    """Delete a floor and all its slots."""
    floor = db.query(models.Floor).filter(
        models.Floor.floor_no == floor_no
    ).first()

    if not floor:
        raise HTTPException(status_code=404, detail=f"Floor {floor_no} not found")

    db.delete(floor)
    db.commit()
    return {"message": f"Floor {floor_no} deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# USER ROUTES — Park, Exit, Search
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/user/park")
def park_vehicle(request: schemas.ParkRequest, db: Session = Depends(get_db)):
    """
    Park a vehicle at a chosen slot.
    - Validates the slot exists and is available
    - Marks slot as occupied
    - Creates vehicle record
    - Adds PARK log entry
    """
    vehicle_no   = request.vehicle_no.upper().strip()
    vehicle_type = request.vehicle_type
    slot_id      = request.slot_id

    # Check if vehicle is already parked
    already = db.query(models.Vehicle).filter(
        models.Vehicle.vehicle_no == vehicle_no,
        models.Vehicle.is_parked  == True
    ).first()
    if already:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle {vehicle_no} is already parked at slot {already.slot_id}"
        )

    # Get the slot
    slot = db.query(models.Slot).filter(models.Slot.slot_id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot {slot_id} not found")
    if slot.is_occupied:
        raise HTTPException(status_code=400, detail=f"Slot {slot_id} is already occupied")

    # Get floor info
    floor = db.query(models.Floor).filter(models.Floor.id == slot.floor_id).first()

    # Mark slot occupied
    slot.is_occupied = True
    slot.vehicle_no  = vehicle_no

    # Create vehicle record
    vehicle = models.Vehicle(
        vehicle_no   = vehicle_no,
        vehicle_type = vehicle_type,
        slot_id      = slot_id,
        floor_no     = floor.floor_no,
        is_parked    = True,
        entry_time   = datetime.now()
    )
    db.add(vehicle)

    # Create log entry
    log = models.ParkingLog(
        vehicle_no = vehicle_no,
        slot_id    = slot_id,
        floor_no   = floor.floor_no,
        action     = "PARK",
        timestamp  = datetime.now()
    )
    db.add(log)

    db.commit()
    return {
        "message":    f"Vehicle {vehicle_no} parked at slot {slot_id}",
        "vehicle_no": vehicle_no,
        "slot_id":    slot_id,
        "floor_no":   floor.floor_no
    }


@app.post("/user/exit", response_model=schemas.ExitResponse)
def exit_vehicle(request: schemas.ExitRequest, db: Session = Depends(get_db)):
    """
    Mark a vehicle as exited.
    - Frees the slot
    - Updates vehicle record
    - Adds EXIT log entry
    - Returns duration in minutes
    """
    vehicle_no = request.vehicle_no.upper().strip()

    # Find parked vehicle
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.vehicle_no == vehicle_no,
        models.Vehicle.is_parked  == True
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"No active parking found for vehicle {vehicle_no}"
        )

    slot_id = vehicle.slot_id

    # Free the slot
    slot = db.query(models.Slot).filter(models.Slot.slot_id == slot_id).first()
    if slot:
        slot.is_occupied = False
        slot.vehicle_no  = None

    # Calculate duration
    exit_time = datetime.now()
    duration  = None
    if vehicle.entry_time:
        diff     = exit_time - vehicle.entry_time
        duration = int(diff.total_seconds() / 60)

    # Update vehicle record
    vehicle.is_parked  = False
    vehicle.exit_time  = exit_time

    # Create EXIT log
    log = models.ParkingLog(
        vehicle_no = vehicle_no,
        slot_id    = slot_id,
        floor_no   = vehicle.floor_no or 0,
        action     = "EXIT",
        timestamp  = exit_time
    )
    db.add(log)
    db.commit()

    return {
        "message":          f"Vehicle {vehicle_no} exited from slot {slot_id}",
        "vehicle_no":       vehicle_no,
        "slot_id":          slot_id,
        "duration_minutes": duration
    }


@app.get("/user/search", response_model=schemas.SearchResponse)
def search_vehicle(veh: str = Query(..., description="Vehicle number"), db: Session = Depends(get_db)):
    """
    Search for a vehicle by number.
    Returns current status, all logs, and any fines.
    """
    veh = veh.upper().strip()

    # Get latest vehicle record (could be parked or historical)
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.vehicle_no == veh
    ).order_by(models.Vehicle.id.desc()).first()

    # Get all logs for this vehicle
    logs = db.query(models.ParkingLog).filter(
        models.ParkingLog.vehicle_no == veh
    ).order_by(models.ParkingLog.timestamp.desc()).all()

    # Get all fines for this vehicle
    fines = db.query(models.Fine).filter(
        models.Fine.vehicle_no == veh
    ).order_by(models.Fine.timestamp.desc()).all()

    return {
        "vehicle": vehicle,
        "logs":    logs,
        "fines":   fines
    }


# ══════════════════════════════════════════════════════════════════════════════
# LOG & FINE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/logs", response_model=List[schemas.LogResponse])
def get_all_logs(
    limit: int = Query(100, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """Returns all parking logs, newest first."""
    return db.query(models.ParkingLog)\
             .order_by(models.ParkingLog.timestamp.desc())\
             .limit(limit)\
             .all()


@app.get("/fines", response_model=List[schemas.FineResponse])
def get_all_fines(db: Session = Depends(get_db)):
    """Returns all fines, newest first."""
    return db.query(models.Fine)\
             .order_by(models.Fine.timestamp.desc())\
             .all()


# ══════════════════════════════════════════════════════════════════════════════
# SENSOR ROUTE — Wrong slot detection
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/sensor/verify", response_model=schemas.SensorVerifyResponse)
def verify_sensor(request: schemas.SensorVerifyRequest, db: Session = Depends(get_db)):
    """
    Sensor check endpoint.
    Compares the slot where the vehicle actually parked (from sensor)
    vs the slot assigned in the system.
    If mismatch → issue ₹100 fine.
    """
    vehicle_no  = request.vehicle_no.upper().strip()
    actual_slot = request.actual_slot.strip()

    # Find the vehicle's assigned slot
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.vehicle_no == vehicle_no,
        models.Vehicle.is_parked  == True
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"No active parking found for vehicle {vehicle_no}"
        )

    assigned_slot = vehicle.slot_id

    # Compare
    if actual_slot != assigned_slot:
        # Issue fine
        fine = models.Fine(
            vehicle_no = vehicle_no,
            amount     = 100,
            reason     = f"Parked at {actual_slot} instead of assigned slot {assigned_slot}",
            timestamp  = datetime.now()
        )
        db.add(fine)
        db.commit()

        return {
            "fine":          True,
            "vehicle_no":    vehicle_no,
            "assigned_slot": assigned_slot,
            "actual_slot":   actual_slot,
            "message":       f"FINE of ₹100 issued. Vehicle parked at {actual_slot} but assigned {assigned_slot}"
        }
    else:
        return {
            "fine":          False,
            "vehicle_no":    vehicle_no,
            "assigned_slot": assigned_slot,
            "actual_slot":   actual_slot,
            "message":       "Correct slot. No fine."
        }


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "status":  "ParkOS API is running",
        "version": "1.0.0",
        "docs":    "Visit /docs for interactive API documentation"
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
