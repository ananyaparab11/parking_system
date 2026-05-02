"""
models.py — SQLAlchemy database models (tables)
Tables: Floor, Slot, Vehicle, ParkingLog, Fine
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Floor(Base):
    """Represents a parking floor."""
    __tablename__ = "floors"

    id           = Column(Integer, primary_key=True, index=True)
    floor_no     = Column(Integer, unique=True, index=True, nullable=False)
    vehicle_type = Column(String, nullable=False)   # 2-Wheeler / 4-Wheeler / 6-Seater
    capacity     = Column(Integer, nullable=False)
    sq_ft        = Column(Float, nullable=False)
    slot_prefix  = Column(String, default="F")

    slots = relationship("Slot", back_populates="floor", cascade="all, delete-orphan")


class Slot(Base):
    """Represents a single parking slot on a floor."""
    __tablename__ = "slots"

    id          = Column(Integer, primary_key=True, index=True)
    slot_id     = Column(String, unique=True, index=True, nullable=False)  # e.g. F1-01
    floor_id    = Column(Integer, ForeignKey("floors.id"), nullable=False)
    is_occupied = Column(Boolean, default=False)
    vehicle_no  = Column(String, nullable=True)   # which vehicle is parked here

    floor = relationship("Floor", back_populates="slots")


class Vehicle(Base):
    """Tracks a vehicle currently parked or historically parked."""
    __tablename__ = "vehicles"

    id           = Column(Integer, primary_key=True, index=True)
    vehicle_no   = Column(String, index=True, nullable=False)
    vehicle_type = Column(String, nullable=False)
    slot_id      = Column(String, nullable=True)
    floor_no     = Column(Integer, nullable=True)
    is_parked    = Column(Boolean, default=True)
    entry_time   = Column(DateTime, default=datetime.now)
    exit_time    = Column(DateTime, nullable=True)


class ParkingLog(Base):
    """Records every PARK and EXIT action."""
    __tablename__ = "parking_logs"

    id         = Column(Integer, primary_key=True, index=True)
    vehicle_no = Column(String, nullable=False)
    slot_id    = Column(String, nullable=False)
    floor_no   = Column(Integer, nullable=False)
    action     = Column(String, nullable=False)   # PARK or EXIT
    timestamp  = Column(DateTime, default=datetime.now)


class Fine(Base):
    """Records fines issued for wrong slot parking."""
    __tablename__ = "fines"

    id         = Column(Integer, primary_key=True, index=True)
    vehicle_no = Column(String, nullable=False)
    amount     = Column(Integer, default=100)
    reason     = Column(String, default="Parked in wrong slot")
    timestamp  = Column(DateTime, default=datetime.now)
