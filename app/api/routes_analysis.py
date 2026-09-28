from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import shutil

from app.config import DATA_DIR
from app.pipeline.video_analyzer import video_analyzer_ai

router = APIRouter(prefix="/api/analysis", tags=["Video Analysis & AI Chat"])

class ChatQueryRequest(BaseModel):
    message: str
    video_name: Optional[str] = None

@router.post("/upload-video")
async def upload_video_file(file: UploadFile = File(...)):
    """Uploads custom video file to data/videos/ directory."""
    if not file.filename.endswith(('.mp4', '.avi', '.mkv', '.mov')):
        raise HTTPException(status_code=400, detail="Invalid video format. Supported: .mp4, .avi, .mkv, .mov")

    videos_dir = DATA_DIR / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    target_path = videos_dir / file.filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Perform AI analysis
    res = video_analyzer_ai.analyze_video(target_path)
    return {
        "success": True,
        "filename": file.filename,
        "file_path": str(target_path),
        "analysis": res.get("summary", "")
    }

@router.post("/chat")
def chat_with_ai(req: ChatQueryRequest):
    """Natural Language AI Chat Q&A on video content."""
    if not req.message:
        raise HTTPException(status_code=400, detail="Message is required")

    reply = video_analyzer_ai.chat_query(req.message, req.video_name)
    return {
        "success": True,
        "response": reply,
        "question": req.message
    }
