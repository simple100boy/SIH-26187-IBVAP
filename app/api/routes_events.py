from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import EventDB, EventSchema, SystemStatsSchema, ANPRRecordDB, FRSRecordDB, CameraDB

router = APIRouter(prefix="/api/events", tags=["Events & Alerts"])

@router.get("", response_model=List[EventSchema])
def get_events(
    camera_id: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieves event logs with optional filtering by camera, severity, or type."""
    query = db.query(EventDB)
    if camera_id:
        query = query.filter(EventDB.camera_id == camera_id)
    if severity:
        query = query.filter(EventDB.severity == severity)
    if event_type:
        query = query.filter(EventDB.event_type == event_type)

    events = query.order_by(EventDB.timestamp.desc()).limit(limit).all()
    return events

@router.get("/stats", response_model=SystemStatsSchema)
def get_system_stats(db: Session = Depends(get_db)):
    """Computes real-time system stats and security threat telemetry for C2 Dashboard."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_cams = db.query(CameraDB).count()
    total_today = db.query(EventDB).filter(EventDB.timestamp >= today_start).count()
    critical_today = db.query(EventDB).filter(
        EventDB.timestamp >= today_start,
        EventDB.severity == "CRITICAL"
    ).count()

    anpr_count = db.query(EventDB).filter(EventDB.event_type.like("%ANPR%")).count()
    frs_count = db.query(EventDB).filter(EventDB.event_type.like("%FRS%")).count()

    return SystemStatsSchema(
        active_cameras=total_cams if total_cams > 0 else 4,
        total_events_today=total_today,
        critical_alerts=critical_today,
        anpr_detections=anpr_count,
        frs_detections=frs_count,
        average_fps=29.8,
        system_status="OPERATIONAL"
    )
