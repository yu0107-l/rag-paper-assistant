from typing import List, Dict, Any


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    A simple character-level splitter.
    It is intentionally lightweight for demo and GitHub display purposes.

    For production, you can replace it with:
    LangChain RecursiveCharacterTextSplitter.
    """
    text = " ".join(text.split())
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == text_len:
            break

        start = max(0, end - chunk_overlap)

    return chunks


def split_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> List[Dict[str, Any]]:
    """
    Split page texts into chunks and keep page metadata.
    """
    all_chunks = []
    global_id = 0

    for page in pages:
        page_num = page["page_num"]
        text = page["text"]
        page_chunks = _split_text(text, chunk_size, chunk_overlap)

        for local_id, chunk_text in enumerate(page_chunks):
            all_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "page_num": page_num,
                    "chunk_id": f"p{page_num}_{local_id}",
                    "global_chunk_id": global_id,
                },
            })
            global_id += 1

    return all_chunks
