# 核心代码说明

这是 RAG 智能论文阅读助手的脱敏展示版核心代码，适合上传到 GitHub 作为项目展示。

## 已包含功能

- Flask API 服务
- PDF 上传与解析
- 文本切分
- OpenAI Embedding 向量化
- ChromaDB 向量存储
- Top-K 相关片段检索
- GPT-4o 问答生成
- SSE 流式输出
- Redis 高频缓存
- Redis 多轮上下文管理

## 本版本说明

- 不包含真实 API Key。
- 不包含真实论文 PDF。
- 不包含本地 ChromaDB 向量库数据。
- Redis 不可用时会自动降级，核心问答链路仍可运行。
