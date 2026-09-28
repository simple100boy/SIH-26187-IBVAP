from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.database import Base

# ==================== SQLAlchemy ORM Models ====================

class CameraDB(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    bop_location = Column(String)  # e.g., "BOP Alpha - North Sector"
    stream_url = Column(String)
    status = Column(String, default="ONLINE")  # ONLINE, OFFLINE, WARNING
    resolution = Column(String, default="1080p")
    fps = Column(Integer, default=30)
    night_enhancement = Column(Boolean, default=False)
    thermal_palette = Column(String, default="ironbow")
    created_at = Column(DateTime, default=datetime.utcnow)


class EventDB(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String, index=True)
    camera_name = Column(String)
    event_type = Column(String, index=True)  # INTRUSION, TRIPWIRE_CROSS, LOITERING, ANPR_MATCH, FRS_MATCH, UNATTENDED_OBJECT
    severity = Column(String, index=True)    # CRITICAL, HIGH, MEDIUM, LOW
    object_class = Column(String)            # Person, Vehicle, Truck, Unknown
    track_id = Column(Integer, nullable=True)
    description = Column(Text)
    anpr_plate = Column(String, nullable=True)
    face_name = Column(String, nullable=True)
    bounding_box = Column(String, nullable=True)  # JSON [x1, y1, x2, y2]
    snapshot_url = Column(String, nullable=True)
    confidence = Column(Float, default=0.90)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ZoneDB(Base):
    __tablename__ = "zones"

    id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    zone_name = Column(String)
    zone_type = Column(String)  # restricted_zone, virtual_tripwire
    coordinates = Column(Text)  # JSON normalized coordinates [[x1, y1], [x2, y2], ...]
    severity = Column(String, default="HIGH")
    enabled = Column(Boolean, default=True)


class ANPRRecordDB(Base):
    __tablename__ = "anpr_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String, index=True)
    plate_number = Column(String, index=True)
    vehicle_type = Column(String)
    confidence = Column(Float)
    snapshot_url = Column(String, nullable=True)
    is_flagged = Column(Boolean, default=False)
    owner_info = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FRSRecordDB(Base):
    __tablename__ = "frs_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String, index=True)
    person_name = Column(String, index=True)
    identity_status = Column(String)  # WATCHLISTED, BORDER_PATROL, UNKNOWN
    match_confidence = Column(Float)
    snapshot_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ==================== Pydantic Schemas ====================

class CameraSchema(BaseModel):
    id: str
    name: str
    bop_location: str
    stream_url: str
    status: str = "ONLINE"
    resolution: str = "1080p"
    fps: int = 30
    night_enhancement: bool = False
    thermal_palette: str = "ironbow"

    class Config:
        from_attributes = True


class EventSchema(BaseModel):
    id: int
    camera_id: str
    camera_name: str
    event_type: str
    severity: str
    object_class: str
    track_id: Optional[int] = None
    description: str
    anpr_plate: Optional[str] = None
    face_name: Optional[str] = None
    snapshot_url: Optional[str] = None
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True


class ZoneCreateSchema(BaseModel):
    id: str
    camera_id: str
    zone_name: str
    zone_type: str  # restricted_zone or virtual_tripwire
    coordinates: List[List[float]]  # list of [x, y] in ratio 0.0-1.0
    severity: str = "HIGH"
    enabled: bool = True


class ZoneSchema(ZoneCreateSchema):
    class Config:
        from_attributes = True


class SystemStatsSchema(BaseModel):
    active_cameras: int
    total_events_today: int
    critical_alerts: int
    anpr_detections: int
    frs_detections: int
    average_fps: float
    system_status: str = "OPERATIONAL"
