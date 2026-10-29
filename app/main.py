import os
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.asr import asr_service, decode_samples

app = FastAPI(title="Local Speech to Text")
BASE_DIR = Path(__file__).resolve().parent.parent
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {".wav", ".webm", ".ogg", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".flac"}
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


async def run_transcription(file: UploadFile, language: str):
    if language not in {"zh", "en"}:
        raise HTTPException(400, "language 必须为 zh 或 en")
    suffix = Path(file.filename or "audio.wav").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(415, "不支持的音频格式")
    data = await file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(400, "音频文件为空")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "音频文件不能超过 10 MB")
    start = time.perf_counter()
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(data)
            path = temp.name
        samples = decode_samples(path)
        duration = len(samples) / 16000
        if duration <= 0:
            raise HTTPException(400, "无法解码音频或音频时长为零")
        if duration > 60:
            raise HTTPException(400, "音频时长不能超过 60 秒")
        try:
            text = asr_service.transcribe(path, language)
        except Exception as exc:
            raise HTTPException(503, f"本地模型不可用或识别失败：{exc}") from exc
        return {"text": text, "language": language, "duration_seconds": round(duration, 2),
                "processing_seconds": round(time.perf_counter() - start, 2)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, f"音频处理失败：{exc}") from exc
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = Form(...)):
    return await run_transcription(file, language)
