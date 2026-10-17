"""
SQLAlchemy engine, session factory, and declarative base.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called once on application startup."""
    from app.models import paper, chat, note  # noqa: F401 (ensure models are registered)

    Base.metadata.create_all(bind=engine)
