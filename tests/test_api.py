import io
import wave
from fastapi.testclient import TestClient
from app.main import app
from app import main
from app.asr import to_simplified_chinese

client = TestClient(app)

def test_chinese_output_is_simplified():
    assert to_simplified_chinese('大家好，今天天氣很好，我們去公園。') == '大家好，今天天气很好，我们去公园。'

def wav_bytes():
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b'\0\0' * 16000)
    return out.getvalue()

def test_health_and_page():
    assert client.get('/health').json() == {'status': 'ok'}
    assert client.get('/').status_code == 200

def test_invalid_language():
    r = client.post('/api/transcribe', files={'file': ('a.wav', wav_bytes(), 'audio/wav')}, data={'language':'fr'})
    assert r.status_code == 400

def test_empty_and_unsupported():
    assert client.post('/api/transcribe', files={'file': ('a.wav', b'', 'audio/wav')}, data={'language':'en'}).status_code == 400
    assert client.post('/api/transcribe', files={'file': ('a.exe', b'x', 'application/octet-stream')}, data={'language':'en'}).status_code == 415

def test_corrupt_audio():
    r = client.post('/api/transcribe', files={'file': ('broken.wav', b'not a wave file', 'audio/wav')}, data={'language':'zh'})
    assert r.status_code == 422

def test_model_error_is_actionable(monkeypatch):
    def fail(*args):
        raise RuntimeError('test model failure')
    monkeypatch.setattr(main.asr_service, 'transcribe', fail)
    r = client.post('/api/transcribe', files={'file': ('a.wav', wav_bytes(), 'audio/wav')}, data={'language':'zh'})
    assert r.status_code == 503
    assert '本地模型不可用' in r.json()['detail']

def test_sample_audio_metadata():
    from pathlib import Path
    for name in ('chinese.wav', 'english.wav'):
        with wave.open(str(Path(__file__).parents[1] / 'samples' / name), 'rb') as w:
            assert w.getnframes() > 0
            assert w.getframerate() > 0

def test_success_mock(monkeypatch):
    monkeypatch.setattr(main.asr_service, 'transcribe', lambda path, language: 'hello' if language == 'en' else '你好')
    r = client.post('/api/transcribe', files={'file': ('a.wav', wav_bytes(), 'audio/wav')}, data={'language':'en'})
    assert r.status_code == 200
    assert r.json()['text'] == 'hello' and r.json()['language'] == 'en'
