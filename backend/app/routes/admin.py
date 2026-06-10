from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models.models import ChatMessage, Document, User

router = APIRouter(prefix="/admin", tags=["Admin"])


def _vector_stats() -> dict:
    """Return lightweight vector DB stats without loading the embedding model."""
    settings = get_settings()
    provider = settings.vector_db_provider.lower()
    stats = {"provider": provider}

    if provider == "chroma":
        try:
            import chromadb

            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            collection = client.get_or_create_collection(settings.chroma_collection)
            stats["collection"] = settings.chroma_collection
            stats["persist_dir"] = settings.chroma_persist_dir
            stats["vector_count"] = collection.count()
        except Exception as exc:
            stats["error"] = str(exc)
        return stats

    if provider == "qdrant":
        stats["collection"] = settings.qdrant_collection
        stats["note"] = "Use Qdrant dashboard or API for detailed counts."
        return stats

    if provider == "pinecone":
        stats["index"] = settings.pinecone_index_name
        stats["note"] = "Use Pinecone console for detailed counts."
        return stats

    stats["error"] = f"Unsupported provider: {provider}"
    return stats


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return {
        "users": db.query(User).count(),
        "documents": db.query(Document).count(),
        "chat_messages": db.query(ChatMessage).count(),
        "recent_documents": [
            d.filename for d in db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
        ],
        "vector_stats": _vector_stats(),
    }
