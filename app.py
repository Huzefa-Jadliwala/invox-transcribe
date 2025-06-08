from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import tempfile

app = FastAPI()

model = WhisperModel("base", compute_type="auto")

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(await audio.read())
        temp_audio.flush()

        segments, _ = model.transcribe(temp_audio.name)
        transcript = " ".join([segment.text for segment in segments])

    return JSONResponse(content={"text": transcript})
