import hashlib
import os
from pathlib import Path
from typing import Dict, Any

from flask import Blueprint, request, jsonify, Response, stream_with_context

from config import Config
from rag.pdf_loader import load_pdf_pages
from rag.text_splitter import split_pages
from rag.vector_store import VectorStore
from rag.qa_chain import answer_question, stream_answer_question
from cache.redis_cache import RedisCache


bp = Blueprint("api", __name__)

Config.ensure_dirs()
vector_store = VectorStore()
cache = RedisCache()


def _make_paper_id(filename: str, content: bytes) -> str:
    digest = hashlib.md5(content).hexdigest()[:12]
    safe_name = Path(filename).stem.replace(" ", "_")[:32]
    return f"{safe_name}_{digest}"


@bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "vector_store": "chroma",
        "collection": Config.COLLECTION_NAME,
    })


@bp.post("/papers/upload")
def upload_paper():
    """
    Upload a PDF, parse pages, split chunks, embed chunks and save them into ChromaDB.

    form-data:
      file: PDF file
    """
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "only PDF files are supported"}), 400

    content = file.read()
    if not content:
        return jsonify({"error": "empty file"}), 400

    paper_id = _make_paper_id(file.filename, content)
    save_path = Config.UPLOAD_DIR / f"{paper_id}.pdf"
    save_path.write_bytes(content)

    pages = load_pdf_pages(save_path)
    chunks = split_pages(
        pages,
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
    )

    for chunk in chunks:
        chunk["metadata"]["paper_id"] = paper_id
        chunk["metadata"]["source_file"] = file.filename

    vector_store.add_chunks(chunks)

    return jsonify({
        "message": "uploaded and indexed successfully",
        "paper_id": paper_id,
        "filename": file.filename,
        "pages": len(pages),
        "chunks": len(chunks),
    })


@bp.post("/papers/ask")
def ask_paper():
    """
    Ask a question about an indexed paper.

    JSON body:
    {
      "paper_id": "xxx",
      "question": "What is the main contribution?",
      "stream": false
    }
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    paper_id = data.get("paper_id")
    question = data.get("question")
    use_stream = bool(data.get("stream", False))

    if not paper_id or not question:
        return jsonify({"error": "paper_id and question are required"}), 400

    cached = cache.get_answer(paper_id, question)
    if cached and not use_stream:
        return jsonify({
            "paper_id": paper_id,
            "question": question,
            "answer": cached["answer"],
            "sources": cached.get("sources", []),
            "cached": True,
        })

    docs = vector_store.search(question, paper_id=paper_id, top_k=Config.TOP_K)

    if not docs:
        return jsonify({
            "paper_id": paper_id,
            "question": question,
            "answer": "没有检索到该论文的相关片段。请先上传并索引 PDF。",
            "sources": [],
            "cached": False,
        })

    history = cache.get_history(paper_id)

    if use_stream:
        def generate():
            full_text = ""
            for token in stream_answer_question(question, docs, history):
                full_text += token
                yield f"data: {token}\n\n"
            sources = [
                {
                    "page": d["metadata"].get("page_num"),
                    "chunk_id": d["metadata"].get("chunk_id"),
                    "source_file": d["metadata"].get("source_file"),
                }
                for d in docs
            ]
            cache.set_answer(paper_id, question, full_text, sources)
            cache.append_history(paper_id, question, full_text)
            yield "data: [DONE]\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    result = answer_question(question, docs, history)
    sources = [
        {
            "page": d["metadata"].get("page_num"),
            "chunk_id": d["metadata"].get("chunk_id"),
            "source_file": d["metadata"].get("source_file"),
        }
        for d in docs
    ]

    cache.set_answer(paper_id, question, result, sources)
    cache.append_history(paper_id, question, result)

    return jsonify({
        "paper_id": paper_id,
        "question": question,
        "answer": result,
        "sources": sources,
        "cached": False,
    })
