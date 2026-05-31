import hashlib
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from config import Config


class VectorStore:
    """
    ChromaDB wrapper:
    - generate embeddings using OpenAI
    - store PDF chunks
    - retrieve Top-K chunks with paper_id filter
    """

    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing. Please set it in .env.")

        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

        self.chroma_client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        response = self.openai_client.embeddings.create(
            model=Config.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    @staticmethod
    def _make_id(text: str, metadata: Dict[str, Any]) -> str:
        raw = f"{metadata.get('paper_id', '')}-{metadata.get('chunk_id', '')}-{text[:50]}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [self._make_id(c["text"], c["metadata"]) for c in chunks]

        embeddings = self._embed(texts)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        paper_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        query_embedding = self._embed([query])[0]

        where = {"paper_id": paper_id} if paper_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        docs = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for text, metadata, distance in zip(documents, metadatas, distances):
            docs.append({
                "text": text,
                "metadata": metadata,
                "score": 1 - float(distance),
            })

        return docs
