from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.models import Document, User
from app.services.document_loader import chunk_pages, extract_text
from app.services.vector_store import add_chunks, delete_document_vectors

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for file in files:
        safe_name = Path(file.filename or "uploaded_file").name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

        target = upload_dir / f"{user.id}_{uuid4().hex}_{safe_name}"
        target.write_bytes(await file.read())

        doc = Document(filename=safe_name, filetype=suffix, path=str(target), owner_id=user.id, chunk_count=0)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            pages = extract_text(str(target))
            chunks = chunk_pages(pages)
            if not chunks:
                raise ValueError("No readable text was extracted from this file.")
            count = add_chunks(chunks, safe_name, doc.id, user.id)
            doc.chunk_count = count
            db.commit()
        except Exception as exc:
            db.delete(doc)
            db.commit()
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Failed to index {safe_name}: {exc}") from exc

        saved.append({"id": doc.id, "filename": doc.filename, "chunks": doc.chunk_count})

    return {"uploaded": saved}


@router.get("/list")
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Document)
    if not user.is_admin:
        query = query.filter(Document.owner_id == user.id)
    docs = query.order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "filetype": d.filetype,
            "chunks": d.chunk_count,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.delete("/delete/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not user.is_admin and doc.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    try:
        delete_document_vectors(doc.id, doc.chunk_count)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete vectors: {exc}") from exc

    Path(doc.path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    return {"message": "Document and vectors deleted successfully."}
