import os
import time
import uuid

TEST_SECRET = "secreto-de-pruebas-secreto-de-pruebas-0123456789"
os.environ["SUPABASE_JWT_SECRET"] = TEST_SECRET  # antes de importar la app

import jwt
import pytest
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
def auth():
    return lambda token: {"Authorization": f"Bearer {token}"}