from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path

from app.config import APP_TITLE, VERSION, SNAPSHOT_DIR, BASE_DIR
from app.database import engine, Base
from app.api.routes_cameras import router as cameras_router
from app.api.routes_events import router as events_router
from app.api.routes_zones import router as zones_router
from app.api.routes_blockchain import router as blockchain_router
from app.api.routes_analysis import router as analysis_router
from app.api.websocket import ws_manager
from app.pipeline.stream_manager import stream_manager

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Check if executing in Vercel serverless environment
IS_VERCEL = os.getenv("VERCEL") is not None or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("==================================================================")
    print(f"  Starting {APP_TITLE} (v{VERSION})")
    print(f"  Environment: {'Vercel Serverless' if IS_VERCEL else 'Local Standalone'}")
    print("==================================================================")

    # Only start background threads if running locally
    if not IS_VERCEL:
        stream_manager.set_websocket_manager(ws_manager)
        stream_manager.start_all()

    yield

    if not IS_VERCEL:
        print("Shutting down Camera Stream Processors...")
        stream_manager.stop_all()

app = FastAPI(
    title=APP_TITLE,
    version=VERSION,
    lifespan=lifespan
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Snapshots
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

snapshots_dir = BASE_DIR / "data" / "snapshots"
snapshots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=str(snapshots_dir)), name="snapshots")

# Register API Routers
app.include_router(cameras_router)
app.include_router(events_router)
app.include_router(zones_router)
app.include_router(blockchain_router)
app.include_router(analysis_router)

# WebSocket Endpoint
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Serve C2 Command & Control Dashboard HTML
@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>IBVAP Command & Control Dashboard API Ready</h1>")
