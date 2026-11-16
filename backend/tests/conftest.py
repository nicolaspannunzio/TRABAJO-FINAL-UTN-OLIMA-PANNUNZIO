import os
import time
import uuid
from urllib.parse import urlparse

import pytest

TEST_SECRET = "secreto-de-pruebas-secreto-de-pruebas-0123456789"
_HOSTS_LOCALES = {"localhost", "127.0.0.1", "::1"}


def _fijar_base_de_pruebas() -> None:
    """Los tests escriben y borran filas: solo pueden correr contra una base local.

    Se ignora DATABASE_URL (que puede venir de backend/.env y apuntar a Supabase).
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.exit("Falta TEST_DATABASE_URL: los tests no usan DATABASE_URL.", returncode=2)
    host = urlparse(url).hostname
    if host not in _HOSTS_LOCALES:
        pytest.exit(f"TEST_DATABASE_URL apunta a '{host}', no a una base local. Abortado.",
                    returncode=2)
    os.environ["DATABASE_URL"] = url


# Antes de importar la app: las variables de entorno pisan a backend/.env
_fijar_base_de_pruebas()
os.environ["SUPABASE_JWT_SECRET"] = TEST_SECRET

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import get_engine
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    """Session sobre la base de pruebas. Lo no confirmado se descarta al cerrar."""
    with Session(get_engine()) as session:
        yield session


@pytest.fixture
def crear_usuario():
    creados = []

    def _crear(rol: str = "operador", activo: bool = True) -> uuid.UUID:
        uid = uuid.uuid4()
        with get_engine().begin() as conn:
            conn.execute(text("INSERT INTO auth.users (id) VALUES (:id)"), {"id": uid})
            conn.execute(
                text("""INSERT INTO usuario (id, nombre, email, rol_id, activo)
                        VALUES (:id, :nombre, :email,
                                (SELECT id FROM rol WHERE nombre = :rol), :activo)"""),
                {"id": uid, "nombre": f"Test {rol}", "email": f"{uid}@test.local",
                 "rol": rol, "activo": activo},
            )
        creados.append(uid)
        return uid

    yield _crear

    with get_engine().begin() as conn:
        for uid in creados:
            conn.execute(text("DELETE FROM auditoria WHERE usuario_id = :id"), {"id": uid})
            conn.execute(text("DELETE FROM usuario WHERE id = :id"), {"id": uid})
            conn.execute(text("DELETE FROM auth.users WHERE id = :id"), {"id": uid})


@pytest.fixture
def make_token():
    def _token(uid, expira_en: int = 3600, secret: str = TEST_SECRET) -> str:
        claims = {"sub": str(uid), "aud": "authenticated", "role": "authenticated",
                  "exp": int(time.time()) + expira_en}
        return jwt.encode(claims, secret, algorithm="HS256")
    return _token

@pytest.fixture
def make_raw_token():
    """Token firmado con los claims exactos que se pasen (para casos inválidos)."""
    def _token(claims: dict) -> str:
        return jwt.encode(claims, TEST_SECRET, algorithm="HS256")
    return _token

@pytest.fixture
def auth():
    return lambda token: {"Authorization": f"Bearer {token}"}