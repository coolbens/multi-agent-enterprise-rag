# Vector Database Connection Guide

## 1. ChromaDB Local Setup
ChromaDB is the default provider.

`.env`:
```env
VECTOR_DB_PROVIDER=chroma
CHROMA_COLLECTION=enterprise_docs
```

Run the backend. Chroma stores vectors locally in `chroma_db/`.

## 2. Pinecone Setup
1. Create a Pinecone account.
2. Create an index.
3. Add your API key and index name.

`.env`:
```env
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=enterprise-docs
```

Restart the backend.

## 3. Qdrant Setup
Local Docker:
```bash
docker compose up qdrant
```

`.env`:
```env
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=enterprise_docs
```

Restart the backend.

## 4. Switch Providers
Change only `VECTOR_DB_PROVIDER` and the matching provider variables. Re-upload documents after switching because each provider has its own storage.
