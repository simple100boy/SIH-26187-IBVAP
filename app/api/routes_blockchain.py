from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import time

from app.database import get_db
from app.models import EventDB
from app.pipeline.blockchain_vault import blockchain_vault

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain & Evidence"])

class VerifyEvidenceRequest(BaseModel):
    snapshot_url: str
    sha256_hash: str

@router.post("/verify-evidence")
def verify_evidence(req: VerifyEvidenceRequest):
    """Verifies evidence file hash on disk against on-chain anchored value."""
    is_valid, message = blockchain_vault.verify_evidence_integrity(req.snapshot_url, req.sha256_hash)
    return {
        "success": True,
        "is_valid": is_valid,
        "message": message,
        "ipfs_cid": blockchain_vault.generate_ipfs_cid(req.sha256_hash),
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

@router.get("/report/{event_id}")
def download_incident_report(event_id: int, db: Session = Depends(get_db)):
    """Generates official IBVAP incident audit report with cryptographic proof."""
    event = db.query(EventDB).filter(EventDB.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Incident not found")

    event_dict = {
        "id": event.id,
        "camera_id": event.camera_id,
        "camera_name": event.camera_name,
        "event_type": event.event_type,
        "severity": event.severity,
        "object_class": event.object_class,
        "track_id": event.track_id,
        "description": event.description,
        "anpr_plate": event.anpr_plate,
        "face_name": event.face_name,
        "snapshot_url": event.snapshot_url
    }

    report_text = blockchain_vault.generate_pdf_report(event_dict)
    filename = f"report_incident_{event_id}.txt"

    return Response(
        content=report_text,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
