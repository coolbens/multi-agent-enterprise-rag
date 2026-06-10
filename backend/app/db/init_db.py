from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.db.session import Base, engine
from app.models.models import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_admin(db: Session) -> None:
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        db.add(User(email="admin@example.com", hashed_password=hash_password("admin123"), is_admin=True))
        db.commit()
