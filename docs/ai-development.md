# OpenCode 开发记录

OpenCode 用于需求拆分、方案实现及自动化测试。重要决策：使用本地 faster-whisper multilingual small CPU int8；采用标准 HTTP multipart API；先交付必做能力，再加入 HTTP 短片段实时识别。生成代码通过接口测试和手动审查约束输入、错误提示及离线模型路径。已知优先改进项是目标 Windows 环境真实模型验证、实时片段边界处理及提供有授权的语音样本。
