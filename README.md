# IBVAP - Intelligent Border Video Analytics Platform

**Transforming Existing CCTV Infrastructure into an AI-Powered Intelligent Surveillance Network for Border Out Posts (BOPs) & Strategic Installations.**

---

## 📌 Project Overview
Border security forces deploy standard CCTV cameras at Border Out Posts (BOPs), checkposts, perimeter roads, and strategic installations. However, conventional CCTV systems primarily provide passive video recording and live monitoring, requiring continuous human observation. Advanced capabilities such as Facial Recognition Systems (FRS), Automatic Number Plate Recognition (ANPR), intrusion detection, and object tracking traditionally require expensive specialized hardware and proprietary smart cameras, making large-scale deployment cost-prohibitive in remote border regions.

**IBVAP (Intelligent Border Video Analytics Platform)** is a software-defined AI platform that ingests live video streams from standard IP-based CCTV cameras and performs real-time computer vision video analytics without requiring dedicated smart-camera hardware.

---

## 🔥 Key System Capabilities
- **Human & Vehicle Detection & Tracking**: Real-time object detection powered by **YOLO11** and multi-object tracking via **ByteTrack / IoU Tracker**.
- **Virtual Tripwire & Zone Intrusion Detection**: Real-time line-crossing and polygon restricted area intrusion alerts with directional vector analysis.
- **Automatic Number Plate Recognition (ANPR)**: Automatic vehicle license plate extraction, OCR, and cross-matching against security hotlists.
- **Facial Recognition System (FRS)**: Face detection, feature signature matching, and security watchlist alerts (Infiltrator, Smuggler, Authorized Patrol).
- **Night-Vision & Thermal Video Enhancement**: Contrast-Limited Adaptive Histogram Equalization (CLAHE), contrast stretching, and pseudo-thermal palette mapping (Ironbow, Jet, Inferno).
- **Suspicious Activity & Loitering Analytics**: Real-time detection of loitering dwell time and unattended objects.
- **Command & Control (C2) Center Dashboard**: High-impact tactical UI with multi-camera grid matrix, interactive canvas tripwire drawer, live audio-visual incident ticker, and evidence locker.

---

## 🏗️ Technical Architecture
```
+------------------+     +--------------------------+     +---------------------------+
|  Existing CCTV   | --> | Video Stream Ingestion   | --> | Low-Light & Thermal AI    |
| (Standard RTSP)  |     | (Multi-Camera Pipeline)  |     | (CLAHE / Ironbow Palette) |
+------------------+     +--------------------------+     +---------------------------+
                                                                        |
                                                                        v
+------------------+     +--------------------------+     +---------------------------+
| Command Center   | <-- | FastAPI + WebSockets     | <-- | YOLO11 + ByteTrack AI     |
| Dashboard (C2)   |     | (Real-Time Alert Push)   |     | Spatial & ANPR/FRS Engine |
+------------------+     +--------------------------+     +---------------------------+
                                    |
                                    v
                         +--------------------------+
                         | SQLite & Snapshot Storage|
                         | (Timestamped Evidence)   |
                         +--------------------------+
```

---

## ⚡ Quick Start Guide

### 1. Requirements
- **Python 3.10+**
- Packages: `fastapi`, `uvicorn`, `opencv-python`, `ultralytics`, `torch`, `easyocr`, `sqlalchemy`, `pydantic`

### 2. Launch the IBVAP C2 Platform
Run the launcher script:
```bash
python run.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 📂 Project Directory Structure
```
SIH IDEA 101/
├── app/
│   ├── config.py              # System configuration & threshold defaults
│   ├── database.py            # SQLite database session & ORM Base
│   ├── models.py              # Pydantic schemas & SQLAlchemy ORM models
│   ├── main.py                # FastAPI web app, lifespan & routes
│   ├── video_generator.py     # Realistic synthetic border CCTV stream generator
│   ├── api/
│   │   ├── routes_cameras.py  # Stream endpoints & MJPEG feed generator
│   │   ├── routes_events.py   # Event logs, search & telemetry stats
│   │   ├── routes_zones.py    # Tripwire & Zone configuration CRUD
│   │   └── websocket.py       # WebSocket manager for live alert streaming
│   └── pipeline/
│       ├── enhancement.py     # CLAHE & thermal palette night vision engine
│       ├── detector.py        # YOLO11 & ByteTrack object tracking engine
│       ├── spatial_analytics.py# Polygon zone intrusion & line tripwire crossing
│       ├── anpr_engine.py     # Vehicle license plate detection & OCR
│       ├── frs_engine.py      # Face detection & watchlist matching engine
│       ├── incident_manager.py# Alert scoring, snapshot generator & DB logger
│       └── stream_manager.py  # Multi-camera thread-safe processor
├── static/
│   ├── css/style.css          # Tactical Military C2 UI styling
│   ├── js/dashboard.js        # Main C2 Center logic & WebSocket client
│   ├── js/canvas_editor.js    # Interactive point-and-click tripwire drawer
│   └── index.html             # Command & Control Center UI
├── data/
│   ├── ibvap.db               # SQLite Database
│   └── snapshots/             # Timestamped evidence snapshots with overlays
├── run.py                     # Convenience launcher script
└── README.md                  # Project documentation
```

---

## 🏆 SIH Pitching Highlights
1. **Cost Elimination**: Converts $50 existing CCTV cameras into AI smart cameras without purchasing $2,000+ proprietary FRS/ANPR camera hardware.
2. **Software-Defined Edge Computing**: Can run locally at remote Border Out Posts (BOPs) with edge AI accelerators (NVIDIA Jetson, Intel NUC, or standard PC).
3. **Zero-Hardware Demo Mode**: Built-in realistic synthetic border video generator allows instant, zero-setup demonstration for hackathon judges and security forces.
