import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Detect Vercel Serverless environment
IS_VERCEL = os.getenv("VERCEL") is not None or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_VERCEL:
    # On Vercel, writeable files must reside in /tmp
    DATA_DIR = Path("/tmp/data")
    SNAPSHOT_DIR = Path("/tmp/snapshots")
    DB_PATH = Path("/tmp/ibvap.db")
else:
    DATA_DIR = BASE_DIR / "data"
    SNAPSHOT_DIR = DATA_DIR / "snapshots"
    DB_PATH = DATA_DIR / "ibvap.db"

# Create directories safely
DATA_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings
APP_TITLE = "IBVAP - Intelligent Border Video Analytics Platform"
VERSION = "1.0.0"
HOST = "0.0.0.0"
PORT = 8000

# Model & AI Config
YOLO_MODEL_NAME = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.45
IOU_THRESHOLD = 0.40

# Target classes for Border Analytics
DETECTION_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    15: "cat",
    16: "dog",
    24: "backpack",
    26: "handbag",
    28: "suitcase"
}

PERSON_CLASSES = [0]
VEHICLE_CLASSES = [2, 3, 5, 7]
UNATTENDED_OBJECT_CLASSES = [24, 26, 28]

# Low-Light & Thermal Simulation Settings
THERMAL_PALETTES = ["jet", "inferno", "ironbow", "grayscale"]
DEFAULT_THERMAL_PALETTE = "ironbow"

# Security Severity Levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
