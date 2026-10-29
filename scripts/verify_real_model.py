"""Run actual local model checks against the bundled Chinese and English samples."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

for language, filename in (("zh", "chinese.wav"), ("en", "english.wav")):
    with (ROOT / "samples" / filename).open("rb") as audio:
        response = client.post(
            "/api/transcribe",
            data={"language": language},
            files={"file": (filename, audio, "audio/wav")},
        )
    response.raise_for_status()
    print(f"{filename}: {response.json()}")
