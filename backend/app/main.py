from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.init_db import ensure_admin, init_db
from app.db.session import SessionLocal
from app.routes import admin, auth, chat, documents

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_admin(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
