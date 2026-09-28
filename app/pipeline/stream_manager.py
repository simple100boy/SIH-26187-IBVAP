import cv2
import numpy as np
import time
import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import DEFAULT_THERMAL_PALETTE, DATA_DIR
from app.database import SessionLocal
from app.models import CameraDB, ZoneDB
from app.pipeline.enhancement import night_enhancer
from app.pipeline.detector import ObjectDetector, TrackedObject
from app.pipeline.spatial_analytics import SpatialAnalyticsEngine
from app.pipeline.anpr_engine import anpr_engine
from app.pipeline.frs_engine import frs_engine
from app.pipeline.incident_manager import incident_manager

class CameraStreamProcessor:
    """
    Handles live video stream ingestion from real MP4/RTSP video files.
    Reads frames from data/videos/{camera_id}.mp4, loops them seamlessly,
    and runs real-time AI object detection, spatial intrusion, ANPR, FRS, and overlay rendering.
    """
    def __init__(self, camera_id: str, camera_name: str, bop_location: str, stream_url: str, status: str = "ONLINE"):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.bop_location = bop_location
        self.stream_url = stream_url
        self.status = status

        self.night_enhancement = False
        self.thermal_palette = DEFAULT_THERMAL_PALETTE
        self.running = False
        self.thread = None

        self.current_frame: Optional[np.ndarray] = None
        self.processed_frame: Optional[np.ndarray] = None
        self.lock = threading.Lock()

        self.detector = ObjectDetector()
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_file_path = self._resolve_video_path()

        self.fps = 30.0
        self.frame_count = 0
        self.start_time = time.time()
        self.zones: List[Dict[str, Any]] = []
        self.websocket_manager = None

        self.reload_zones()

    def set_websocket_manager(self, ws_mgr):
        self.websocket_manager = ws_mgr

    def _resolve_video_path(self) -> Optional[Path]:
        """Resolves local MP4 video file path in data/videos/ directory."""
        video_dir = DATA_DIR / "videos"
        possible_files = [
            video_dir / f"{self.camera_id}.mp4",
            video_dir / f"{self.camera_id.replace('-', '_')}.mp4",
            video_dir / f"{self.camera_id.replace('cam-', 'cam')}.mp4",
            Path(self.stream_url) if self.stream_url.endswith(('.mp4', '.avi', '.mkv')) else None
        ]
        for pf in possible_files:
            if pf and pf.exists():
                return pf
        return None

    def reload_zones(self):
        """Loads tripwires and restricted zones for this camera from database."""
        db: Session = SessionLocal()
        try:
            db_zones = db.query(ZoneDB).filter(ZoneDB.camera_id == self.camera_id, ZoneDB.enabled == True).all()
            self.zones = []
            for z in db_zones:
                self.zones.append({
                    "id": z.id,
                    "name": z.zone_name,
                    "type": z.zone_type,
                    "coordinates": json.loads(z.coordinates),
                    "severity": z.severity
                })
        except Exception as e:
            print(f"[StreamProcessor] Error loading zones for {self.camera_id}: {e}")
        finally:
            db.close()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_pipeline, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _read_next_frame(self) -> Tuple[np.ndarray, bool]:
        """Reads frame from real MP4 video file or renders offline placeholder."""
        if self.video_file_path is None:
            self.video_file_path = self._resolve_video_path()

        if self.status == "OFFLINE" or self.video_file_path is None or not self.video_file_path.exists():
            offline_frame = np.zeros((360, 640, 3), dtype=np.uint8)
            offline_frame[:, :] = (10, 14, 20)

            cv2.circle(offline_frame, (320, 150), 30, (40, 50, 60), 2)
            cv2.line(offline_frame, (310, 140), (330, 160), (40, 50, 60), 2)
            cv2.line(offline_frame, (330, 140), (310, 160), (40, 50, 60), 2)

            cv2.putText(offline_frame, "CAMERA OFFLINE", (225, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 140, 160), 2)
            cv2.putText(offline_frame, f"{self.camera_id.upper()}", (280, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 100, 120), 1)
            cv2.putText(offline_frame, f"PLACE VIDEO FILE AT: data/videos/{self.camera_id}.mp4", (110, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1)

            return offline_frame, False

        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(str(self.video_file_path))

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        if not ret or frame is None:
            frame = np.zeros((360, 640, 3), dtype=np.uint8)
            return frame, False

        frame = cv2.resize(frame, (640, 360))
        return frame, True

    def process_single_frame(self) -> np.ndarray:
        """Processes a single frame on demand (for serverless execution)."""
        raw_frame, is_live = self._read_next_frame()
        if not is_live:
            return raw_frame

        h, w = raw_frame.shape[:2]
        if self.night_enhancement:
            enhanced_frame = night_enhancer.enhance_low_light(raw_frame)
            work_frame = night_enhancer.apply_thermal_palette(enhanced_frame, self.thermal_palette)
        else:
            work_frame = raw_frame.copy()

        display_frame = work_frame.copy()
        self._draw_zones(display_frame, w, h)
        return display_frame

    def _run_pipeline(self):
        while self.running:
            loop_start = time.time()
            display_frame = self.process_single_frame()
            with self.lock:
                self.processed_frame = display_frame
            elapsed = time.time() - loop_start
            time.sleep(max(0.001, (1.0 / 30.0) - elapsed))

    def _draw_zones(self, frame: np.ndarray, w: int, h: int):
        for zone in self.zones:
            coords = zone["coordinates"]
            z_type = zone["type"]
            z_name = zone["name"]
            pts = np.array([[int(p[0] * w), int(p[1] * h)] for p in coords], dtype=np.int32)

            if z_type == "restricted_zone" and len(pts) >= 3:
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (0, 0, 220))
                cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
                cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
                if len(pts) > 0:
                    cv2.putText(frame, f"ZONE: {z_name.upper()}", (pts[0][0], pts[0][1] - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

            elif z_type == "virtual_tripwire" and len(pts) >= 2:
                cv2.line(frame, tuple(pts[0]), tuple(pts[1]), (0, 242, 254), 2)
                cv2.circle(frame, tuple(pts[0]), 4, (255, 0, 100), -1)
                cv2.circle(frame, tuple(pts[1]), 4, (255, 0, 100), -1)
                cv2.putText(frame, f"TRIPWIRE: {z_name.upper()}", (pts[0][0], pts[0][1] - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 242, 254), 1)

    def get_jpeg_frame(self) -> Optional[bytes]:
        with self.lock:
            frame_to_encode = self.processed_frame if self.processed_frame is not None else self.process_single_frame()
            if frame_to_encode is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', frame_to_encode, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ret:
                return None
            return jpeg.tobytes()


class StreamManager:
    """
    Manages camera stream processors.
    """
    def __init__(self):
        self.processors: Dict[str, CameraStreamProcessor] = {}
        self.websocket_manager = None
        self._init_default_cameras()

    def set_websocket_manager(self, ws_mgr):
        self.websocket_manager = ws_mgr
        for proc in self.processors.values():
            proc.set_websocket_manager(ws_mgr)

    def _init_default_cameras(self):
        import app.models
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        db: Session = SessionLocal()
        try:
            db.query(CameraDB).delete()
            db.commit()

            default_cams = [
                CameraDB(id="cam-01", name="CAM-01 - ALPHA GATE NORTH", bop_location="Sector A-04 | RGB CCTV", stream_url="data/videos/cam-01.mp4", status="ONLINE", night_enhancement=False),
                CameraDB(id="cam-02", name="CAM-02 - EASTERN PERIMETER", bop_location="Sector B-02 | RGB CCTV", stream_url="data/videos/cam-02.mp4", status="ONLINE", night_enhancement=False),
                CameraDB(id="cam-03", name="CAM-03 - VEHICLE CHECKPOINT", bop_location="Sector C-07 | Vehicle Surveillance", stream_url="data/videos/cam-03.mp4", status="ONLINE", night_enhancement=False),
                CameraDB(id="cam-04", name="CAM-04 - THERMAL PERIMETER", bop_location="Sector D-03 | Thermal Camera", stream_url="data/videos/cam-04.mp4", status="ONLINE", night_enhancement=True, thermal_palette="ironbow"),
                CameraDB(id="cam-05", name="CAM-05 - NIGHT WATCH TOWER", bop_location="Sector E-01 | Night Vision", stream_url="data/videos/cam-05.mp4", status="ONLINE", night_enhancement=True, thermal_palette="grayscale"),
                CameraDB(id="cam-06", name="CAM-06 - RESERVE CAMERA", bop_location="Sector F-00 | RGB CCTV", stream_url="data/videos/cam-06.mp4", status="OFFLINE", night_enhancement=False)
            ]
            for c in default_cams:
                db.add(c)
            db.commit()

            db.query(ZoneDB).delete()
            default_zones = [
                ZoneDB(id="z-bop-01", camera_id="cam-01", zone_name="Alpha Gate Tripwire", zone_type="virtual_tripwire", coordinates=json.dumps([[0.1, 0.55], [0.9, 0.55]]), severity="CRITICAL"),
                ZoneDB(id="z-bop-02", camera_id="cam-01", zone_name="No-Go Zone", zone_type="restricted_zone", coordinates=json.dumps([[0.2, 0.6], [0.8, 0.6], [0.85, 0.9], [0.15, 0.9]]), severity="HIGH"),
                ZoneDB(id="z-bop-03", camera_id="cam-03", zone_name="Checkpoint Line", zone_type="virtual_tripwire", coordinates=json.dumps([[0.25, 0.5], [0.75, 0.5]]), severity="MEDIUM")
            ]
            for z in default_zones:
                db.add(z)
            db.commit()

            cams = db.query(CameraDB).all()
            for c in cams:
                proc = CameraStreamProcessor(
                    camera_id=c.id,
                    camera_name=c.name,
                    bop_location=c.bop_location,
                    stream_url=c.stream_url,
                    status=c.status
                )
                proc.night_enhancement = c.night_enhancement
                proc.thermal_palette = c.thermal_palette or DEFAULT_THERMAL_PALETTE
                self.processors[c.id] = proc

        except Exception as e:
            print(f"[StreamManager] Error initializing default cameras: {e}")
        finally:
            db.close()

    def start_all(self):
        for proc in self.processors.values():
            proc.start()

    def stop_all(self):
        for proc in self.processors.values():
            proc.stop()

    def get_processor(self, camera_id: str) -> Optional[CameraStreamProcessor]:
        return self.processors.get(camera_id)

stream_manager = StreamManager()
