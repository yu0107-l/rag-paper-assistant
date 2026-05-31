# 系统架构说明

本项目采用典型 RAG 架构，主要包括文档解析、文本切分、向量化、向量存储、检索增强生成、上下文管理和缓存优化几个部分。

## 处理流程

1. 用户上传 PDF 论文。
2. 系统使用 PyMuPDF 解析 PDF 文本。
3. 使用 RecursiveCharacterTextSplitter 将论文切分为多个 chunk。
4. 调用 OpenAI text-embedding-3-small 生成 chunk 向量。
5. 将向量和 metadata 写入 ChromaDB。
6. 用户输入问题后，系统对问题进行向量化。
7. 从 ChromaDB 中检索 Top-K 相关片段。
8. 将检索结果、历史对话和问题拼接进 Prompt。
9. 调用 GPT-4o 生成回答。
10. 通过 SSE 将回答流式返回给用户。
11. Redis 负责维护多轮上下文和高频问题缓存。
