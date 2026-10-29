"""Lazy-loaded local Whisper ASR backend."""
import os
import threading


def decode_samples(audio_path: str):
    """Decode any supported container to mono float32 samples at 16 kHz."""
    import av
    import numpy as np

    decoded = []
    with av.open(audio_path, mode="r") as container:
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if audio_stream is None:
            raise ValueError("文件中没有音轨")
        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        for frame in container.decode(audio_stream):
            decoded.extend(item.to_ndarray().reshape(-1) for item in resampler.resample(frame))
        decoded.extend(item.to_ndarray().reshape(-1) for item in resampler.resample(None))
    if not decoded:
        raise ValueError("音频中没有有效采样")
    return np.concatenate(decoded).astype(np.float32) / 32768.0


def to_simplified_chinese(text: str) -> str:
    from opencc import OpenCC

    return OpenCC("t2s").convert(text)


class ASRService:
    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

    def transcribe(self, audio_path: str, language: str) -> str:
        try:
            with self._lock:
                if self._model is None:
                    from faster_whisper import WhisperModel
                    name = os.getenv("ASR_MODEL", "small")
                    cache = os.getenv("ASR_MODEL_DIR")
                    self._model = WhisperModel(name, device="cpu", compute_type="int8", download_root=cache)
                samples = decode_samples(audio_path)
                segments, _ = self._model.transcribe(samples, language=language, beam_size=5, vad_filter=True)
                text = "".join(segment.text for segment in segments).strip()
                if language == "zh" and text:
                    text = to_simplified_chinese(text)
                return text
        except Exception as exc:
            raise RuntimeError(f"本地语音模型加载或识别失败：{exc}") from exc


asr_service = ASRService()
