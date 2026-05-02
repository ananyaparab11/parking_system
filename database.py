"""
database.py — Database connection setup using SQLAlchemy + SQLite
SQLite stores everything in a single file: parking.db
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./parking.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get DB session in each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
