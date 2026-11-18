"""A2 / HU-02: gestión de usuarios (RN-02, RN-03, RN-24).

La Admin API de Supabase Auth se reemplaza por un doble (FakeAuthAdmin) que escribe en el
`auth.users` simulado de la base de pruebas, porque usuario.id tiene FK hacia esa tabla.
"""
import uuid

import pytest
from sqlalchemy import text

from app.core.db import get_engine
from app.main import app
from app.modules.usuarios import repository
from app.modules.usuarios.auth_admin import AuthAdminError, get_auth_admin

CONTRASENA = "clave-inicial-123"


# --- Doble de la Admin API -----------------------------------------------------

class FakeAuthAdmin:
    def __init__(self, falla_con: AuthAdminError | None = None):
        self.falla_con = falla_con
        self.creados: list[uuid.UUID] = []
        self.eliminados: list[uuid.UUID] = []

    def crear_usuario(self, email: str, contrasena: str) -> uuid.UUID:
        if self.falla_con:
            raise self.falla_con
        uid = uuid.uuid4()
        with get_engine().begin() as conn:
            conn.execute(text("INSERT INTO auth.users (id) VALUES (:id)"), {"id": uid})
        self.creados.append(uid)
        return uid

    def eliminar_usuario(self, usuario_id: uuid.UUID) -> None:
        self.eliminados.append(usuario_id)
        with get_engine().begin() as conn:
            conn.execute(text("DELETE FROM auth.users WHERE id = :id"), {"id": usuario_id})


def _instalar(fake: FakeAuthAdmin) -> None:
    app.dependency_overrides[get_auth_admin] = lambda: fake


# --- Fixtures ------------------------------------------------------------------

@pytest.fixture
def admin(crear_usuario, make_token, auth):
    """Un admin con sus headers. Pide crear_usuario primero: su limpieza corre después."""
    uid = crear_usuario("admin")
    return {"uid": uid, "headers": auth(make_token(uid))}


@pytest.fixture
def auth_fake():
    """Doble de la Admin API instalado en la app. Al terminar borra lo que creó por la API."""
    fake = FakeAuthAdmin()
    _instalar(fake)
    yield fake
    app.dependency_overrides.pop(get_auth_admin, None)
    ids = [str(i) for i in fake.creados]
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM usuario WHERE id::text = ANY(:ids)"), {"ids": ids})
        conn.execute(text("DELETE FROM auth.users WHERE id::text = ANY(:ids)"), {"ids": ids})


def _email() -> str:
    return f"nuevo-{uuid.uuid4().hex[:8]}@test.local"


def _alta(client, admin, email=None, rol="operador", nombre="Persona Nueva"):
    return client.post("/usuarios", headers=admin["headers"], json={
        "email": email or _email(), "nombre": nombre, "rol": rol, "contrasena": CONTRASENA})


def _fila(uid):
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT u.id, u.email, u.nombre, u.activo, r.nombre AS rol
                    FROM usuario u JOIN rol r ON r.id = u.rol_id WHERE u.id = :id"""),
            {"id": uid}).mappings().first()


def _auditoria(usuario_id, accion):
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT usuario_id, entidad, entidad_id, detalle FROM auditoria
                    WHERE accion = :a AND entidad_id = :e"""),
            {"a": accion, "e": usuario_id}).mappings().all()


def _existe_en_auth(uid) -> bool:
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT 1 FROM auth.users WHERE id = :id"),
                            {"id": uid}).first() is not None


# --- Criterio 1: el alta crea la cuenta y la fila con el mismo id --------------

def test_alta_crea_cuenta_y_fila_con_el_mismo_id(client, admin, auth_fake):
    email = _email()
    r = _alta(client, admin, email=email, rol="operador", nombre="Ana Gómez")

    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["email"] == email and cuerpo["rol"] == "operador" and cuerpo["activo"] is True
    assert "contrasena" not in cuerpo

    assert len(auth_fake.creados) == 1
    uid = auth_fake.creados[0]
    assert cuerpo["id"] == str(uid)
    assert _existe_en_auth(uid)
    fila = _fila(uid)
    assert fila["email"] == email and fila["rol"] == "operador" and fila["nombre"] == "Ana Gómez"


def test_alta_audita_con_el_admin_y_sin_la_contrasena(client, admin, auth_fake):
    r = _alta(client, admin, rol="admin")
    uid = uuid.UUID(r.json()["id"])

    filas = _auditoria(uid, "alta_usuario")
    assert len(filas) == 1
    assert filas[0]["usuario_id"] == admin["uid"] and filas[0]["entidad"] == "usuario"
    assert filas[0]["detalle"]["rol"] == "admin"
    assert CONTRASENA not in str(filas[0]["detalle"])


def test_alta_guarda_el_email_en_minusculas(client, admin, auth_fake):
    r = _alta(client, admin, email=f"MAYUS-{uuid.uuid4().hex[:6]}@Test.Local")
    assert r.status_code == 201
    assert r.json()["email"] == r.json()["email"].lower()


# --- Criterio 2: si el insert falla, no queda la cuenta en Auth -----------------

def test_email_repetido_en_la_base_compensa_y_devuelve_409(client, admin, auth_fake, crear_usuario):
    existente = crear_usuario("operador")
    email_repetido = _fila(existente)["email"]

    r = _alta(client, admin, email=email_repetido)

    assert r.status_code == 409 and r.json()["codigo"] == "email_duplicado"
    assert len(auth_fake.creados) == 1
    huerfano = auth_fake.creados[0]
    assert auth_fake.eliminados == [huerfano]  # se borró la cuenta recién creada
    assert not _existe_en_auth(huerfano)
    assert _auditoria(huerfano, "alta_usuario") == []  # el rollback descartó la auditoría


def test_fallo_inesperado_del_insert_compensa_y_devuelve_500(client, admin, auth_fake, monkeypatch):
    def romper(*args, **kwargs):
        raise RuntimeError("falla simulada del insert")
    monkeypatch.setattr(repository, "insertar", romper)

    r = _alta(client, admin)

    assert r.status_code == 500 and r.json()["codigo"] == "error_interno"
    assert auth_fake.eliminados == auth_fake.creados and len(auth_fake.creados) == 1
    assert not _existe_en_auth(auth_fake.creados[0])


def test_si_falla_la_compensacion_igual_responde_500(client, admin, auth_fake, monkeypatch):
    """Limitación documentada: queda un id huérfano en Auth, que se loguea."""
    def romper_insert(*args, **kwargs):
        raise RuntimeError("falla simulada del insert")

    def romper_borrado(usuario_id):
        raise AuthAdminError("Auth caído")
    monkeypatch.setattr(repository, "insertar", romper_insert)
    monkeypatch.setattr(auth_fake, "eliminar_usuario", romper_borrado)

    r = _alta(client, admin)

    assert r.status_code == 500 and r.json()["codigo"] == "error_interno"


# --- Fallas de la Admin API: no se crea nada -------------------------------------

def test_falla_de_la_admin_api_devuelve_502_y_no_crea_nada(client, admin, auth_fake):
    auth_fake.falla_con = AuthAdminError("Supabase Auth respondió 500")
    email = _email()

    r = _alta(client, admin, email=email)

    assert r.status_code == 502 and r.json()["codigo"] == "auth_error"
    with get_engine().connect() as conn:
        assert conn.execute(text("SELECT 1 FROM usuario WHERE email = :e"), {"e": email}).first() is None


def test_email_ya_existente_en_auth_devuelve_409(client, admin, auth_fake):
    auth_fake.falla_con = AuthAdminError("ya existe", "email_exists")
    r = _alta(client, admin)
    assert r.status_code == 409 and r.json()["codigo"] == "email_duplicado"


def test_contrasena_debil_segun_auth_devuelve_422(client, admin, auth_fake):
    auth_fake.falla_con = AuthAdminError("débil", "weak_password")
    r = _alta(client, admin)
    assert r.status_code == 422 and r.json()["codigo"] == "contrasena_invalida"


@pytest.mark.parametrize("cuerpo", [
    {"email": "sin-arroba", "nombre": "X", "rol": "operador", "contrasena": CONTRASENA},
    {"email": "a@b.co", "nombre": "", "rol": "operador", "contrasena": CONTRASENA},
    {"email": "a@b.co", "nombre": "X", "rol": "superadmin", "contrasena": CONTRASENA},
    {"email": "a@b.co", "nombre": "X", "rol": "operador", "contrasena": "corta"},
])
def test_alta_con_datos_invalidos_devuelve_422(client, admin, auth_fake, cuerpo):
    r = client.post("/usuarios", headers=admin["headers"], json=cuerpo)
    assert r.status_code == 422 and r.json()["codigo"] == "validacion"
    assert auth_fake.creados == []


# --- Criterio 3: la baja es lógica y queda en auditoría --------------------------

def test_baja_deja_activo_false_sin_borrar_la_fila_y_audita(client, admin, auth_fake):
    uid = uuid.UUID(_alta(client, admin).json()["id"])

    r = client.post(f"/usuarios/{uid}/baja", headers=admin["headers"])

    assert r.status_code == 200 and r.json()["activo"] is False
    assert _fila(uid)["activo"] is False  # la fila sigue ahí
    filas = _auditoria(uid, "baja_usuario")
    assert len(filas) == 1 and filas[0]["usuario_id"] == admin["uid"]


def test_baja_es_idempotente_y_no_audita_dos_veces(client, admin, auth_fake):
    uid = uuid.UUID(_alta(client, admin).json()["id"])
    client.post(f"/usuarios/{uid}/baja", headers=admin["headers"])

    r = client.post(f"/usuarios/{uid}/baja", headers=admin["headers"])

    assert r.status_code == 200 and r.json()["activo"] is False
    assert len(_auditoria(uid, "baja_usuario")) == 1


def test_usuario_dado_de_baja_recibe_403_usuario_inactivo(client, admin, auth_fake, make_token, auth):
    uid = uuid.UUID(_alta(client, admin).json()["id"])
    client.post(f"/usuarios/{uid}/baja", headers=admin["headers"])

    r = client.get("/me", headers=auth(make_token(uid)))

    assert r.status_code == 403 and r.json()["codigo"] == "usuario_inactivo"


def test_baja_de_usuario_inexistente_devuelve_404(client, admin):
    r = client.post(f"/usuarios/{uuid.uuid4()}/baja", headers=admin["headers"])
    assert r.status_code == 404 and r.json()["codigo"] == "usuario_no_encontrado"


# --- Edición y listado ------------------------------------------------------------

def test_editar_nombre_y_rol_audita_antes_y_despues(client, admin, auth_fake):
    uid = uuid.UUID(_alta(client, admin, rol="operador", nombre="Nombre Viejo").json()["id"])

    r = client.patch(f"/usuarios/{uid}", headers=admin["headers"],
                     json={"nombre": "Nombre Nuevo", "rol": "admin"})

    assert r.status_code == 200
    assert r.json()["nombre"] == "Nombre Nuevo" and r.json()["rol"] == "admin"
    assert _fila(uid)["rol"] == "admin"
    detalle = _auditoria(uid, "edicion_usuario")[0]["detalle"]
    assert detalle["antes"] == {"nombre": "Nombre Viejo", "rol": "operador"}
    assert detalle["despues"] == {"nombre": "Nombre Nuevo", "rol": "admin"}


def test_editar_sin_cambios_no_audita(client, admin, auth_fake):
    uid = uuid.UUID(_alta(client, admin, nombre="Igual").json()["id"])
    r = client.patch(f"/usuarios/{uid}", headers=admin["headers"], json={"nombre": "Igual"})
    assert r.status_code == 200
    assert _auditoria(uid, "edicion_usuario") == []


def test_editar_usuario_inexistente_devuelve_404(client, admin):
    r = client.patch(f"/usuarios/{uuid.uuid4()}", headers=admin["headers"], json={"nombre": "X"})
    assert r.status_code == 404


def test_editar_con_rol_invalido_devuelve_422(client, admin, auth_fake):
    uid = uuid.UUID(_alta(client, admin).json()["id"])
    r = client.patch(f"/usuarios/{uid}", headers=admin["headers"], json={"rol": "superadmin"})
    assert r.status_code == 422


def test_listar_incluye_al_usuario_creado(client, admin, auth_fake):
    uid = _alta(client, admin).json()["id"]
    r = client.get("/usuarios", headers=admin["headers"])
    assert r.status_code == 200
    assert uid in [u["id"] for u in r.json()]


# --- Un admin no se deja sin acceso a sí mismo --------------------------------------

def test_admin_no_puede_darse_de_baja_a_si_mismo(client, admin):
    r = client.post(f"/usuarios/{admin['uid']}/baja", headers=admin["headers"])

    assert r.status_code == 409 and r.json()["codigo"] == "autoedicion_no_permitida"
    assert _fila(admin["uid"])["activo"] is True
    assert _auditoria(admin["uid"], "baja_usuario") == []


def test_admin_no_puede_cambiarse_el_propio_rol(client, admin):
    r = client.patch(f"/usuarios/{admin['uid']}", headers=admin["headers"], json={"rol": "operador"})

    assert r.status_code == 409 and r.json()["codigo"] == "autoedicion_no_permitida"
    assert _fila(admin["uid"])["rol"] == "admin"
    assert _auditoria(admin["uid"], "edicion_usuario") == []


def test_admin_si_puede_editar_su_propio_nombre(client, admin):
    # Mandar su mismo rol no es un cambio de rol: se permite.
    r = client.patch(f"/usuarios/{admin['uid']}", headers=admin["headers"],
                     json={"nombre": "Mi Nombre Nuevo", "rol": "admin"})

    assert r.status_code == 200 and r.json()["nombre"] == "Mi Nombre Nuevo"


def test_admin_si_puede_dar_de_baja_a_otro_admin(client, admin, auth_fake):
    otro = uuid.UUID(_alta(client, admin, rol="admin").json()["id"])

    r = client.post(f"/usuarios/{otro}/baja", headers=admin["headers"])

    assert r.status_code == 200 and r.json()["activo"] is False


# --- El operador recibe 403 en todo --------------------------------------------------

def test_operador_recibe_403_y_no_se_crea_nada(client, crear_usuario, make_token, auth, auth_fake):
    operador = crear_usuario("operador")
    headers = auth(make_token(operador))
    otro = uuid.uuid4()

    respuestas = [
        client.get("/usuarios", headers=headers),
        client.post("/usuarios", headers=headers, json={
            "email": _email(), "nombre": "X", "rol": "operador", "contrasena": CONTRASENA}),
        client.patch(f"/usuarios/{otro}", headers=headers, json={"nombre": "X"}),
        client.post(f"/usuarios/{otro}/baja", headers=headers),
    ]

    for r in respuestas:
        assert r.status_code == 403 and r.json()["codigo"] == "permiso_insuficiente"
    assert auth_fake.creados == []
