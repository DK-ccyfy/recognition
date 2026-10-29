# Local AI Speech-to-Text

Python 3.12 + FastAPI + 原生 HTML/JS。CPU 本地模型识别中文/英文，支持浏览器录音、音频上传及实验性分片实时识别。不会调用云端 ASR 或浏览器语音识别 API。

## 启动

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 。首次识别会下载 faster-whisper `small` 权重，需网络；下载完成后模型缓存可离线运行。可用 `ASR_MODEL_DIR` 指定缓存目录，或用 `ASR_MODEL` 选择其他兼容模型。CPU int8 推理。

API：`GET /health`；`POST /api/transcribe` multipart 字段 `file`、`language`（zh/en）。支持 WAV、WebM、OGG、MP3、M4A、FLAC 等，最大 10 MB、时长不超过 60 秒。

## 测试

```sh
python -m pytest -q
```

这是不下载模型的 Mock/API 测试。真实模型验证：启动服务后分别上传中文和英文 WAV，或执行：

```sh
curl -F file=@samples/chinese.wav -F language=zh http://127.0.0.1:8000/api/transcribe
curl -F file=@samples/english.wav -F language=en http://127.0.0.1:8000/api/transcribe
```

也可直接通过本机 API 客户端运行真实模型集成验证（首次运行会下载模型）：

```sh
python scripts/verify_real_model.py
```

麦克风权限、浏览器上传、拒绝权限与断网验证需在 Chrome/Edge 实际操作；详见 `docs/test-report.md`。实时选项按约 4 秒发送一段，属于近实时实验方案。
