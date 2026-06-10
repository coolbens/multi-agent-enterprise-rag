from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


def get_embeddings():
    """Return the configured embedding model."""
    settings = get_settings()
    if settings.embedding_provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    return HuggingFaceEmbeddings(model_name=settings.huggingface_embedding_model)


def get_vectorstore():
    """Create a vector store client based on VECTOR_DB_PROVIDER."""
    settings = get_settings()
    provider = settings.vector_db_provider.lower()
    embeddings = get_embeddings()

    if provider == "chroma":
        return Chroma(
            collection_name=settings.chroma_collection,
            persist_directory=settings.chroma_persist_dir,
            embedding_function=embeddings,
        )

    if provider == "pinecone":
        # Requires a Pinecone index already created with the same dimension as the embedding model.
        from pinecone import Pinecone
        from langchain_community.vectorstores import Pinecone as PineconeVectorStore

        if not settings.pinecone_api_key or not settings.pinecone_index_name:
            raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME are required")

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        return PineconeVectorStore(index, embeddings.embed_query, "text")

    if provider == "qdrant":
        from langchain_community.vectorstores import Qdrant
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        if not settings.qdrant_url:
            raise ValueError("QDRANT_URL is required when VECTOR_DB_PROVIDER=qdrant")

        if not settings.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY is required when VECTOR_DB_PROVIDER=qdrant")

        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60,
        )

        vector_size = len(embeddings.embed_query("test"))

        try:
            client.get_collection(settings.qdrant_collection)
        except Exception:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
            ),
        )
        return Qdrant(
            client=client,
            collection_name=settings.qdrant_collection,
            embeddings=embeddings,
        )
    
    raise ValueError(f"Unsupported VECTOR_DB_PROVIDER: {provider}")

def add_chunks(chunks: list[dict], filename: str, document_id: int, owner_id: int) -> int:
    vectorstore = get_vectorstore()
    docs: list[Document] = []
    ids: list[str] = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"doc-{document_id}-chunk-{i}"
        ids.append(chunk_id)
        docs.append(
            Document(
                page_content=chunk["text"],
                metadata={
                    "source": filename,
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "page": chunk.get("page", "unknown"),
                    "chunk_id": chunk_id,
                },
            )
        )

    if docs:
        vectorstore.add_documents(docs, ids=ids)
        if hasattr(vectorstore, "persist"):
            vectorstore.persist()

    return len(docs)


def _matches_owner(item: dict[str, Any], owner_id: int | None) -> bool:
    if owner_id is None:
        return True
    return item.get("metadata", {}).get("owner_id") == owner_id


def similarity_search(question: str, top_k: int = 5, owner_id: int | None = None) -> list[dict[str, Any]]:
    """Search relevant chunks.

    owner_id is important because it prevents one user from retrieving another user's
    private document chunks.
    """
    vectorstore = get_vectorstore()
    metadata_filter = {"owner_id": owner_id} if owner_id is not None else None

    try:
        if metadata_filter:
            results = vectorstore.similarity_search_with_score(question, k=top_k, filter=metadata_filter)
        else:
            results = vectorstore.similarity_search_with_score(question, k=top_k)
    except TypeError:
        # Some vector store integrations use different filter signatures.
        # Fall back to a wider search and filter manually.
        results = vectorstore.similarity_search_with_score(question, k=max(top_k * 5, top_k))

    items = [{"content": doc.page_content, "metadata": doc.metadata, "score": score} for doc, score in results]
    items = [item for item in items if _matches_owner(item, owner_id)]
    return items[:top_k]


def delete_document_vectors(document_id: int, chunk_count: int) -> None:
    """Delete vectors for a document when the backend knows their generated IDs."""
    if chunk_count <= 0:
        return

    vectorstore = get_vectorstore()
    ids = [f"doc-{document_id}-chunk-{i}" for i in range(chunk_count)]

    if hasattr(vectorstore, "delete"):
        vectorstore.delete(ids=ids)
        if hasattr(vectorstore, "persist"):
            vectorstore.persist()
