import cv2
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import SNAPSHOT_DIR, SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW
from app.database import SessionLocal
from app.models import EventDB, ANPRRecordDB, FRSRecordDB

class IncidentManager:
    """
    Manages security alerts, incident logging, evidence snapshot generation,
    and real-time WebSocket broadcast dispatch.
    """
    def __init__(self):
        self.alert_cooldowns: Dict[str, float] = {}  # key: "cam_id:track_id:event_type" -> timestamp
        self.cooldown_seconds = 4.0

    def trigger_incident(
        self,
        camera_id: str,
        camera_name: str,
        event_type: str,
        severity: str,
        object_class: str,
        track_id: Optional[int],
        description: str,
        frame: Optional[cv2.Mat] = None,
        bounding_box: Optional[list] = None,
        anpr_plate: Optional[str] = None,
        face_name: Optional[str] = None,
        confidence: float = 0.90,
        websocket_manager = None
    ) -> Optional[Dict[str, Any]]:

        # Deduplication check
        cooldown_key = f"{camera_id}:{track_id}:{event_type}"
        current_time = time.time()

        if cooldown_key in self.alert_cooldowns:
            if current_time - self.alert_cooldowns[cooldown_key] < self.cooldown_seconds:
                return None  # Suppress duplicate alert

        self.alert_cooldowns[cooldown_key] = current_time

        # Generate Evidence Snapshot
        snapshot_filename = f"ev_{int(current_time)}_{camera_id}_{event_type}.jpg"
        snapshot_path = SNAPSHOT_DIR / snapshot_filename
        snapshot_relative_url = f"/snapshots/{snapshot_filename}"

        if frame is not None and frame.size > 0:
            annotated = frame.copy()
            # Draw overlay timestamp & watermark
            h, w = annotated.shape[:2]
            cv2.rectangle(annotated, (0, h - 40), (w, h), (15, 23, 42), -1)
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text = f"IBVAP EVIDENCE LOCKER | {camera_name} | {event_type} | {ts_str}"
            cv2.putText(annotated, text, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 242, 254), 2)
            cv2.imwrite(str(snapshot_path), annotated)
        else:
            snapshot_relative_url = None

        # Save to SQLite Database
        db: Session = SessionLocal()
        try:
            db_event = EventDB(
                camera_id=camera_id,
                camera_name=camera_name,
                event_type=event_type,
                severity=severity,
                object_class=object_class,
                track_id=track_id,
                description=description,
                anpr_plate=anpr_plate,
                face_name=face_name,
                bounding_box=json.dumps(bounding_box) if bounding_box else None,
                snapshot_url=snapshot_relative_url,
                confidence=confidence,
                timestamp=datetime.utcnow()
            )
            db.add(db_event)
            db.commit()
            db.refresh(db_event)

            event_dict = {
                "id": db_event.id,
                "camera_id": camera_id,
                "camera_name": camera_name,
                "event_type": event_type,
                "severity": severity,
                "object_class": object_class,
                "track_id": track_id,
                "description": description,
                "anpr_plate": anpr_plate,
                "face_name": face_name,
                "snapshot_url": snapshot_relative_url,
                "confidence": confidence,
                "timestamp": db_event.timestamp.strftime("%H:%M:%S")
            }

            # Broadcast over WebSocket
            if websocket_manager is not None:
                websocket_manager.broadcast_sync({
                    "type": "NEW_ALERT",
                    "data": event_dict
                })

            print(f"[IncidentManager] 🚨 ALERT [{severity}] {event_type} on {camera_name}: {description}")
            return event_dict

        except Exception as e:
            print(f"[IncidentManager] Error logging event: {e}")
            db.rollback()
            return None
        finally:
            db.close()

incident_manager = IncidentManager()
