# 测试报告

## 自动化验证

在 macOS arm64、Python 3.14 环境运行 `python -m pytest -q`：**7 passed**。覆盖健康检查、首页、成功（Mock）、语言错误、空文件、不支持格式、损坏 WAV、模型异常和样本 WAV 元数据。常规测试不触发模型下载。`python -m compileall -q app tests` 与 `node --check static/app.js` 均通过。

## 真实模型验证

通过实际 faster-whisper small CPU int8 模型调用 API 成功识别两份随项目提交的样本：

| 样本 | 模型输出 | 音频时长 | 处理耗时 |
|---|---|---:|---:|
| `samples/chinese.wav`（zh） | 大家好,今天天氣很好,我們一起去公園散步吧! | 5.04 秒 | 3.35 秒 |
| `samples/english.wav`（en） | Hello, this is a local speech recognition system running on my computer. It can turn speech into text. | 6.28 秒 | 1.22 秒 |

中文识别采用繁体输出“天氣/我們/公園”，语义与参考文本一致。首次模型加载曾暴露 PyAV 新版本 API 不兼容；改为应用侧 PyAV 解码后，两种语言推理均通过。

## 浏览器验证

实际通过浏览器文件选择器上传两种 WAV：中文、英文均收到 HTTP 200，页面展示识别状态、文本和时长。点击开始录音后浏览器拒绝麦克风权限，页面正确展示权限说明且无控制台错误。覆盖拒绝权限分支，但当前没有可授权的麦克风设备，因此没有声称完成真实麦克风录音或实时识别的端到端验收。

## 尚需目标环境复核

当前执行环境为 macOS arm64 / Python 3.14，而交付目标为 Windows 11 / Python 3.12。Windows 安装、Chrome/Edge 实机麦克风录制（中文和英文）、实时分片过程中连续说话、模型缓存后断网识别尚未在目标机器验证。模型已完成本地推理，但断网测试仍需在目标机确认。无语音音频应返回空文本，静音样本未单独执行。
