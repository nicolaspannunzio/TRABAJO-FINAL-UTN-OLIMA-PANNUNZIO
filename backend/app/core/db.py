from functools import lru_cache

from sqlalchemy import text
from sqlmodel import Session, create_engine

from app.core.config import get_settings


def _normalizar_url(url: str) -> str:
    # SQLAlchemy usa psycopg 2 por defecto; forzamos psycopg 3.
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


@lru_cache
def get_engine():
    s = get_settings()
    return create_engine(
        _normalizar_url(s.database_url),
        pool_size=s.db_pool_size,
        max_overflow=2,
        pool_pre_ping=True,  # descarta conexiones cortadas por Supabase/Render
        connect_args={
            "prepare_threshold": None,  # necesario con el pooler en modo transacción
            "connect_timeout": 5,
        },
    )


def dispose_engine() -> None:
    get_engine().dispose()


def get_session():
    """Dependencia FastAPI: una Session por request.

    No hace commit: cada operación de escritura confirma explícitamente.
    Si no se confirma, al cerrar se descarta (rollback).
    """
    with Session(get_engine()) as session:
        yield session


def check_db() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False