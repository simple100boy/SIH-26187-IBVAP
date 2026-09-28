from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models import CameraDB, CameraSchema
from app.pipeline.stream_manager import stream_manager, CameraStreamProcessor

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraSchema])
def get_cameras(db: Session = Depends(get_db)):
    """Returns list of registered border surveillance CCTV cameras."""
    cameras = db.query(CameraDB).all()
    return cameras

@router.post("/{camera_id}/night_enhancement")
def toggle_night_enhancement(camera_id: str, enabled: bool, palette: str = "ironbow", db: Session = Depends(get_db)):
    """Toggles low-light enhancement and thermal color palette for camera stream."""
    cam = db.query(CameraDB).filter(CameraDB.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    cam.night_enhancement = enabled
    cam.thermal_palette = palette
    db.commit()

    proc = stream_manager.get_processor(camera_id)
    if proc:
        proc.night_enhancement = enabled
        proc.thermal_palette = palette

    return {"status": "success", "camera_id": camera_id, "night_enhancement": enabled, "palette": palette}

def gen_mjpeg_frames(processor: CameraStreamProcessor):
    """Generator function yielding MJPEG frame stream."""
    while True:
        frame_bytes = processor.get_jpeg_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033) # ~30 FPS

@router.get("/feed/{camera_id}")
def video_feed(camera_id: str):
    """Returns live MJPEG video stream with AI overlays."""
    proc = stream_manager.get_processor(camera_id)
    if not proc:
        raise HTTPException(status_code=404, detail="Camera stream not found")

    return StreamingResponse(
        gen_mjpeg_frames(proc),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
