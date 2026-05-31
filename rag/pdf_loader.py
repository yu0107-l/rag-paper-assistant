from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF


def load_pdf_pages(pdf_path: str | Path) -> List[Dict[str, Any]]:
    """
    Parse PDF into page-level text.

    Returns:
        [
            {"page_num": 1, "text": "..."},
            {"page_num": 2, "text": "..."}
        ]
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "page_num": index,
                    "text": text,
                })

    return pages
