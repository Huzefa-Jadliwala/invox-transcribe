import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
import subprocess

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whisper_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic response models
class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str]
    duration: Optional[float]

class HealthResponse(BaseModel):
    status: str
    model: Optional[str]
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str]

# FastAPI app
app = FastAPI(
    title="Whisper Transcription Service",
    version="1.0.0"
)

whisper_model = None

def get_whisper_model(model_name: str = "base") -> WhisperModel:
    global whisper_model

    if whisper_model and whisper_model.model_size_or_path == model_name:
        return whisper_model

    try:
        logger.info(f"Loading Whisper model: {model_name}")
        whisper_model = WhisperModel(model_name, compute_type="auto")
        return whisper_model
    except Exception as e:
        logger.error(f"Model load failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")

def convert_audio_format(input_path: str, output_path: str) -> bool:
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            '-y', output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return False

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        return HealthResponse(
            status="healthy",
            model=os.getenv("WHISPER_MODEL", "base"),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Unhealthy")

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    model: str = Query("base"),
    language: Optional[str] = Query(None)
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = Path(audio.filename).suffix.lower()
    supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.wma', '.aac']

    if file_ext not in supported_formats:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {file_ext}")

    temp_original = None
    temp_converted = None

    try:
        whisper_model = get_whisper_model(model)

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_original:
            content = await audio.read()
            temp_original.write(content)
            temp_original.flush()

        audio_path = temp_original.name

        if file_ext != '.wav':
            temp_converted = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_converted.close()
            if not convert_audio_format(temp_original.name, temp_converted.name):
                raise HTTPException(status_code=500, detail="Audio conversion failed")
            audio_path = temp_converted.name

        segments, info = whisper_model.transcribe(audio_path, language=language if language else None)
        text = " ".join([segment.text.strip() for segment in segments])

        return TranscriptionResponse(
            text=text,
            language=getattr(info, "language", None),
            duration=getattr(info, "duration", None)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        for f in [temp_original, temp_converted]:
            try:
                if f and os.path.exists(f.name):
                    os.unlink(f.name)
            except Exception as e:
                logger.warning(f"Temp file cleanup error: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc)
        ).model_dump()
    )

if __name__ == "__main__":
    try:
        model_name = os.getenv("WHISPER_MODEL", "base")
        get_whisper_model(model_name)
        logger.info(f"Loaded model on startup: {model_name}")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        exit(1)

    uvicorn.run(app, host="0.0.0.0", port=9000)
