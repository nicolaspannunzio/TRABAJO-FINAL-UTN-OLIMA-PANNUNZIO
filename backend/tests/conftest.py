import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest

TEST_SECRET = "secreto-de-pruebas-secreto-de-pruebas-0123456789"
_HOSTS_LOCALES = {"localhost", "127.0.0.1", "::1", "postgres"}
ESQUEMA_SQL = Path(__file__).resolve().parents[2] / "database" / "esquema_completo.sql"

# En Supabase, auth.users la crea Supabase Auth. En la base descartable se simula
# con lo mínimo que necesita la FK usuario.id -> auth.users(id).
AUTH_SIMULADO = """
CREATE SCHEMA auth;
CREATE TABLE auth.users (id UUID PRIMARY KEY);
"""


def _fijar_base_de_pruebas() -> str:
    """Los tests borran y recrean el esquema: solo pueden correr contra una base
    local y descartable (nombre terminado en _test).

    Se ignora DATABASE_URL (que puede venir de backend/.env y apuntar a Supabase).
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.exit("Falta TEST_DATABASE_URL: los tests no usan DATABASE_URL.")
    partes = urlparse(url)
    if partes.hostname not in _HOSTS_LOCALES:
        pytest.exit(f"TEST_DATABASE_URL apunta a '{partes.hostname}', no a una base local. Abortado.")
    nombre_base = partes.path.lstrip("/")
    if not nombre_base.endswith("_test"):
        pytest.exit(f"La base '{nombre_base}' no termina en _test: no se recrea su esquema. Abortado.")
    os.environ["DATABASE_URL"] = url
    return url


def _recrear_esquema(url: str) -> None:
    """Base limpia: auth.users simulado + esquema_completo.sql tal cual (sin create_all)."""
    import psycopg

    url_psycopg = url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url_psycopg, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        conn.execute("DROP SCHEMA IF EXISTS auth CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute(AUTH_SIMULADO)
        # El archivo trae su propio BEGIN/COMMIT: si falla, no queda a medias.
        conn.execute(ESQUEMA_SQL.read_text(encoding="utf-8"))


# Antes de importar la app: las variables de entorno pisan a backend/.env
_TEST_DATABASE_URL = _fijar_base_de_pruebas()
os.environ["SUPABASE_JWT_SECRET"] = TEST_SECRET

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import get_engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def base_de_pruebas():
    """Una vez por corrida: esquema recreado desde database/esquema_completo.sql."""
    _recrear_esquema(_TEST_DATABASE_URL)
    yield
    get_engine().dispose()


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