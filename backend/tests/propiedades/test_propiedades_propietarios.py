"""A3 / HU-03: alta y edición de propiedades y propietarios (RN-05).

Cada test crea sus propios datos (prefijo "A3-test") y los borra al terminar:
no depende de la semilla ni deja filas para otros tests.
"""
import uuid

import pytest
from sqlalchemy import text

from app.core.db import get_engine

PREFIJO = "A3-test"


@pytest.fixture
def headers(crear_usuario, make_token, auth):
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture(autouse=True)
def limpiar():
    yield
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM propiedad WHERE direccion LIKE :p"), {"p": f"{PREFIJO}%"})
        conn.execute(text("DELETE FROM propietario WHERE nombre LIKE :p"), {"p": f"{PREFIJO}%"})


def _direccion() -> str:
    return f"{PREFIJO} Calle {uuid.uuid4().hex[:8]} 123"


# --- Propiedades ---------------------------------------------------------------

def test_propiedad_nueva_queda_activa(client, headers):
    # Criterio 1 de HU-03.
    r = client.post("/propiedades", json={"direccion": _direccion()}, headers=headers)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["estado"] == "activa"
    assert cuerpo["localidad"] is None and cuerpo["fecha_alta"] and cuerpo["id"]
    with get_engine().connect() as conn:
        estado = conn.execute(text("SELECT estado FROM propiedad WHERE id = :i"),
                              {"i": cuerpo["id"]}).scalar_one()
    assert estado == "activa"


def test_propiedad_con_localidad_y_espacios_en_los_bordes(client, headers):
    r = client.post("/propiedades", json={"direccion": f"  {_direccion()}  ",
                                          "localidad": "  Rosario "}, headers=headers)
    assert r.status_code == 201
    assert r.json()["localidad"] == "Rosario"
    assert not r.json()["direccion"].startswith(" ")


@pytest.mark.parametrize("cuerpo", [
    {},
    {"direccion": ""},
    {"direccion": "   "},
    {"direccion": "x", "estado": "borrada"},
])
def test_propiedad_invalida_422(client, headers, cuerpo):
    r = client.post("/propiedades", json=cuerpo, headers=headers)
    assert r.status_code == 422
    assert r.json()["codigo"] == "validacion"


def test_obtener_propiedad_y_aparece_en_la_lista(client, headers):
    creada = client.post("/propiedades", json={"direccion": _direccion()}, headers=headers).json()
    r = client.get(f"/propiedades/{creada['id']}", headers=headers)
    assert r.status_code == 200 and r.json() == creada
    ids = [p["id"] for p in client.get("/propiedades", headers=headers).json()]
    assert creada["id"] in ids


def test_obtener_propiedad_inexistente_404(client, headers):
    r = client.get(f"/propiedades/{uuid.uuid4()}", headers=headers)
    assert r.status_code == 404
    assert r.json()["codigo"] == "propiedad_no_encontrada"


def test_editar_propiedad_solo_cambia_lo_enviado(client, headers):
    creada = client.post("/propiedades", json={"direccion": _direccion(), "localidad": "Rosario"},
                         headers=headers).json()
    r = client.patch(f"/propiedades/{creada['id']}", json={"estado": "inactiva"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "inactiva"
    assert r.json()["direccion"] == creada["direccion"]
    assert r.json()["localidad"] == "Rosario"
    # localidad se puede vaciar enviando null explícito
    r = client.patch(f"/propiedades/{creada['id']}", json={"localidad": None}, headers=headers)
    assert r.json()["localidad"] is None and r.json()["estado"] == "inactiva"


@pytest.mark.parametrize("cuerpo", [{"direccion": None}, {"direccion": " "}, {"estado": None},
                                    {"estado": "borrada"}])
def test_editar_propiedad_invalido_422(client, headers, cuerpo):
    creada = client.post("/propiedades", json={"direccion": _direccion()}, headers=headers).json()
    r = client.patch(f"/propiedades/{creada['id']}", json=cuerpo, headers=headers)
    assert r.status_code == 422
    # no quedó modificada
    assert client.get(f"/propiedades/{creada['id']}", headers=headers).json() == creada


def test_editar_propiedad_inexistente_404(client, headers):
    r = client.patch(f"/propiedades/{uuid.uuid4()}", json={"estado": "inactiva"}, headers=headers)
    assert r.status_code == 404
    assert r.json()["codigo"] == "propiedad_no_encontrada"


# --- Propietarios --------------------------------------------------------------

def _nombre() -> str:
    return f"{PREFIJO} Propietario {uuid.uuid4().hex[:8]}"


def test_crear_propietario(client, headers):
    r = client.post("/propietarios", json={"nombre": _nombre(), "email": "x@test.local"},
                    headers=headers)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["estado"] == "activa"
    assert cuerpo["email"] == "x@test.local"
    assert cuerpo["cuit_dni"] is None and cuerpo["telefono"] is None


@pytest.mark.parametrize("cuerpo", [{}, {"nombre": ""}, {"nombre": "  "}])
def test_propietario_invalido_422(client, headers, cuerpo):
    r = client.post("/propietarios", json=cuerpo, headers=headers)
    assert r.status_code == 422 and r.json()["codigo"] == "validacion"


def test_obtener_y_listar_propietarios(client, headers):
    creado = client.post("/propietarios", json={"nombre": _nombre()}, headers=headers).json()
    assert client.get(f"/propietarios/{creado['id']}", headers=headers).json() == creado
    ids = [p["id"] for p in client.get("/propietarios", headers=headers).json()]
    assert creado["id"] in ids


def test_propietario_inexistente_404(client, headers):
    for r in (client.get(f"/propietarios/{uuid.uuid4()}", headers=headers),
              client.patch(f"/propietarios/{uuid.uuid4()}", json={"nombre": "x"}, headers=headers)):
        assert r.status_code == 404
        assert r.json()["codigo"] == "propietario_no_encontrado"


def test_editar_propietario_parcial(client, headers):
    creado = client.post("/propietarios", json={"nombre": _nombre(), "telefono": "341-555"},
                         headers=headers).json()
    r = client.patch(f"/propietarios/{creado['id']}", json={"cuit_dni": "20-00000000-1"},
                     headers=headers)
    assert r.status_code == 200
    assert r.json()["cuit_dni"] == "20-00000000-1"
    assert r.json()["telefono"] == "341-555" and r.json()["nombre"] == creado["nombre"]
    # un campo opcional vacío se guarda como null
    r = client.patch(f"/propietarios/{creado['id']}", json={"telefono": ""}, headers=headers)
    assert r.json()["telefono"] is None


def test_editar_propietario_nombre_null_422(client, headers):
    creado = client.post("/propietarios", json={"nombre": _nombre()}, headers=headers).json()
    r = client.patch(f"/propietarios/{creado['id']}", json={"nombre": None}, headers=headers)
    assert r.status_code == 422
