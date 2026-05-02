"""
schemas.py — Pydantic models for request validation and response formatting.
These define what data the API accepts and returns.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Floor schemas ─────────────────────────────────────────────────────────────

class FloorCreate(BaseModel):
    floor_no:     int
    vehicle_type: str   # 2-Wheeler / 4-Wheeler / 6-Seater
    capacity:     int
    sq_ft:        float
    slot_prefix:  Optional[str] = None


class FloorResponse(BaseModel):
    floor_no:     int
    vehicle_type: str
    capacity:     int
    sq_ft:        float
    slot_prefix:  str

    class Config:
        from_attributes = True


# ── Slot schemas ──────────────────────────────────────────────────────────────

class SlotResponse(BaseModel):
    slot_id:     str
    is_occupied: bool
    vehicle_no:  Optional[str] = None

    class Config:
        from_attributes = True


class FloorWithSlots(BaseModel):
    floor_no:     int
    vehicle_type: str
    sq_ft:        float
    capacity:     int
    slots:        List[SlotResponse]

    class Config:
        from_attributes = True


# ── Vehicle / Parking schemas ─────────────────────────────────────────────────

class ParkRequest(BaseModel):
    vehicle_no:   str
    vehicle_type: str
    slot_id:      str


class ExitRequest(BaseModel):
    vehicle_no: str


class ExitResponse(BaseModel):
    message:          str
    vehicle_no:       str
    slot_id:          str
    duration_minutes: Optional[int] = None


class VehicleResponse(BaseModel):
    vehicle_no:   str
    vehicle_type: str
    slot_id:      Optional[str]
    floor_no:     Optional[int]
    is_parked:    bool
    entry_time:   Optional[datetime]

    class Config:
        from_attributes = True


# ── Log schemas ───────────────────────────────────────────────────────────────

class LogResponse(BaseModel):
    vehicle_no: str
    slot_id:    str
    floor_no:   int
    action:     str
    timestamp:  datetime

    class Config:
        from_attributes = True


# ── Fine schemas ──────────────────────────────────────────────────────────────

class SensorVerifyRequest(BaseModel):
    vehicle_no:  str
    actual_slot: str


class SensorVerifyResponse(BaseModel):
    fine:          bool
    vehicle_no:    str
    assigned_slot: Optional[str]
    actual_slot:   str
    message:       str


class FineResponse(BaseModel):
    vehicle_no: str
    amount:     int
    reason:     str
    timestamp:  datetime

    class Config:
        from_attributes = True


# ── Search response ───────────────────────────────────────────────────────────

class SearchResponse(BaseModel):
    vehicle: Optional[VehicleResponse]
    logs:    List[LogResponse]
    fines:   List[FineResponse]
