from pathlib import Path
import pandas as pd
from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text(path: str) -> list[dict]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return [{"text": page.extract_text() or "", "page": str(i + 1)} for i, page in enumerate(reader.pages)]
    if suffix == ".docx":
        doc = DocxDocument(str(file_path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return [{"text": text, "page": "docx"}]
    if suffix in [".csv", ".xlsx", ".xls"]:
        df = pd.read_csv(file_path) if suffix == ".csv" else pd.read_excel(file_path)
        return [{"text": df.astype(str).to_csv(index=False), "page": "table"}]
    if suffix == ".txt":
        return [{"text": file_path.read_text(encoding="utf-8", errors="ignore"), "page": "txt"}]
    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_pages(pages: list[dict], chunk_size: int = 900, overlap: int = 150) -> list[dict]:
    chunks = []
    for page in pages:
        text = " ".join(page["text"].split())
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append({"text": chunk_text, "page": page.get("page", "unknown")})
            start = max(end - overlap, end) if overlap >= chunk_size else end - overlap
    return chunks
