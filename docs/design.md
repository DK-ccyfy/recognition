# 设计说明

FastAPI 提供静态页、健康检查及 multipart 转写端点。`app.asr.ASRService` 延迟初始化 faster-whisper 的 multilingual small 模型，CPU int8 推理；模型缓存由 `ASR_MODEL_DIR` 指定，默认使用 faster-whisper 缓存。small 在精度/CPU可用性间折中，模型约数百 MB，首次下载需要网络，准备后离线推理。服务端通过 PyAV 解码 WAV 与浏览器 WebM 等音频，统一转成 16 kHz 单声道 float32，先限制扩展名、大小和时长。前端 MediaRecorder 录音；实时模式将录音拆成短片段并复用同一 API。

实时分片并非原生流式模型：片段之间缺乏上下文、请求可能延迟，后续可改为 WebSocket + 有状态缓冲并对片段边界去重。
