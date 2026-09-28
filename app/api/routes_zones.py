from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app.models import ZoneDB, ZoneSchema, ZoneCreateSchema
from app.pipeline.stream_manager import stream_manager

router = APIRouter(prefix="/api/zones", tags=["Zones & Tripwires"])

@router.get("/{camera_id}", response_model=List[ZoneSchema])
def get_zones_for_camera(camera_id: str, db: Session = Depends(get_db)):
    """Returns configured virtual tripwires and restricted zones for a given camera."""
    zones = db.query(ZoneDB).filter(ZoneDB.camera_id == camera_id).all()
    result = []
    for z in zones:
        result.append(ZoneSchema(
            id=z.id,
            camera_id=z.camera_id,
            zone_name=z.zone_name,
            zone_type=z.zone_type,
            coordinates=json.loads(z.coordinates),
            severity=z.severity,
            enabled=z.enabled
        ))
    return result

@router.post("", response_model=ZoneSchema)
def create_or_update_zone(zone_in: ZoneCreateSchema, db: Session = Depends(get_db)):
    """Saves a new virtual tripwire or polygon restricted zone drawn on the C2 canvas editor."""
    existing = db.query(ZoneDB).filter(ZoneDB.id == zone_in.id).first()
    if existing:
        existing.zone_name = zone_in.zone_name
        existing.zone_type = zone_in.zone_type
        existing.coordinates = json.dumps(zone_in.coordinates)
        existing.severity = zone_in.severity
        existing.enabled = zone_in.enabled
        db.commit()
        db.refresh(existing)
        db_zone = existing
    else:
        db_zone = ZoneDB(
            id=zone_in.id,
            camera_id=zone_in.camera_id,
            zone_name=zone_in.zone_name,
            zone_type=zone_in.zone_type,
            coordinates=json.dumps(zone_in.coordinates),
            severity=zone_in.severity,
            enabled=zone_in.enabled
        )
        db.add(db_zone)
        db.commit()
        db.refresh(db_zone)

    # Reload zones in stream processor
    proc = stream_manager.get_processor(zone_in.camera_id)
    if proc:
        proc.reload_zones()

    return ZoneSchema(
        id=db_zone.id,
        camera_id=db_zone.camera_id,
        zone_name=db_zone.zone_name,
        zone_type=db_zone.zone_type,
        coordinates=json.loads(db_zone.coordinates),
        severity=db_zone.severity,
        enabled=db_zone.enabled
    )

@router.delete("/{zone_id}")
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    """Deletes a zone definition."""
    zone = db.query(ZoneDB).filter(ZoneDB.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    cam_id = zone.camera_id
    db.delete(zone)
    db.commit()

    proc = stream_manager.get_processor(cam_id)
    if proc:
        proc.reload_zones()

    return {"status": "deleted", "zone_id": zone_id}
