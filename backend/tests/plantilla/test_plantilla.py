"""A6 / HU-06: plantilla de conceptos por propiedad (RN-08).

Cada test crea sus propios datos (prefijo "A6-test") y los borra al terminar.
El criterio 2 (un concepto desactivado no aparece en el checklist que se abre después)
necesita la apertura de período de B: se verifica en tests/cross/ (Gate 1).
"""
import uuid

import pytest
from sqlalchemy import text

from app.core.db import get_engine

PREFIJO = "A6-test"


@pytest.fixture
def headers(crear_usuario, make_token, auth):
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture(autouse=True)
def limpiar():
    yield
    with get_engine().begin() as conn:
        p = {"p": f"{PREFIJO}%"}
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id IN "
                          "(SELECT id FROM propiedad WHERE direccion LIKE :p)"), p)
        conn.execute(text("DELETE FROM propiedad WHERE direccion LIKE :p"), p)
        conn.execute(text("DELETE FROM concepto WHERE nombre LIKE :p"), p)


def _propiedad() -> str:
    with get_engine().begin() as conn:
        return str(conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                                {"d": f"{PREFIJO} {uuid.uuid4().hex[:8]}"}).scalar_one())


def _concepto() -> str:
    with get_engine().begin() as conn:
        return str(conn.execute(text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                                {"n": f"{PREFIJO} {uuid.uuid4().hex[:8]}"}).scalar_one())


def _cantidad(propiedad_id: str, concepto_id: str) -> int:
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT count(*) FROM concepto_propiedad "
                                 "WHERE propiedad_id = :p AND concepto_id = :c"),
                            {"p": propiedad_id, "c": concepto_id}).scalar_one()


def _activo_en_base(asociacion_id: str) -> bool:
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT activo FROM concepto_propiedad WHERE id = :i"),
                            {"i": asociacion_id}).scalar_one()


# --- Asociar ---------------------------------------------------------------------------

def test_asociar_crea_la_fila_activa_con_el_nombre_del_concepto(client, headers):
    p, c = _propiedad(), _concepto()
    r = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["propiedad_id"] == p and cuerpo["concepto_id"] == c
    assert cuerpo["activo"] is True and cuerpo["concepto"].startswith(PREFIJO) and cuerpo["id"]


# --- Criterio 1: asociar otra vez se rechaza -----------------------------------------------

def test_asociar_dos_veces_se_rechaza_409_y_queda_una_sola_fila(client, headers):
    p, c = _propiedad(), _concepto()
    assert client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c},
                       headers=headers).status_code == 201
    r = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers)
    assert r.status_code == 409
    assert r.json()["codigo"] == "concepto_ya_asociado"
    assert _cantidad(p, c) == 1


def test_asociar_un_concepto_desactivado_tambien_se_rechaza(client, headers):
    p, c = _propiedad(), _concepto()
    a = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers).json()
    client.patch(f"/propiedades/{p}/conceptos/{a['id']}", json={"activo": False}, headers=headers)
    r = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers)
    assert r.status_code == 409 and r.json()["codigo"] == "concepto_ya_asociado"


def test_el_mismo_concepto_en_otra_propiedad_es_valido(client, headers):
    c = _concepto()
    for p in (_propiedad(), _propiedad()):
        assert client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c},
                           headers=headers).status_code == 201


def test_asociar_a_propiedad_inexistente_404(client, headers):
    r = client.post(f"/propiedades/{uuid.uuid4()}/conceptos", json={"concepto_id": _concepto()},
                    headers=headers)
    assert r.status_code == 404 and r.json()["codigo"] == "propiedad_no_encontrada"


def test_asociar_concepto_inexistente_404(client, headers):
    r = client.post(f"/propiedades/{_propiedad()}/conceptos",
                    json={"concepto_id": str(uuid.uuid4())}, headers=headers)
    assert r.status_code == 404 and r.json()["codigo"] == "concepto_no_encontrado"


def test_asociar_sin_concepto_id_422(client, headers):
    r = client.post(f"/propiedades/{_propiedad()}/conceptos", json={}, headers=headers)
    assert r.status_code == 422 and r.json()["codigo"] == "validacion"


# --- Listar -----------------------------------------------------------------------------------

def test_listar_devuelve_solo_la_plantilla_de_esa_propiedad(client, headers):
    p1, p2, c1, c2 = _propiedad(), _propiedad(), _concepto(), _concepto()
    client.post(f"/propiedades/{p1}/conceptos", json={"concepto_id": c1}, headers=headers)
    client.post(f"/propiedades/{p2}/conceptos", json={"concepto_id": c2}, headers=headers)
    r = client.get(f"/propiedades/{p1}/conceptos", headers=headers)
    assert r.status_code == 200
    assert [f["concepto_id"] for f in r.json()] == [c1]


def test_listar_propiedad_inexistente_404(client, headers):
    r = client.get(f"/propiedades/{uuid.uuid4()}/conceptos", headers=headers)
    assert r.status_code == 404


# --- Activar y desactivar ---------------------------------------------------------------------

def test_desactivar_y_reactivar_un_concepto(client, headers):
    p, c = _propiedad(), _concepto()
    a = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers).json()

    r = client.patch(f"/propiedades/{p}/conceptos/{a['id']}", json={"activo": False}, headers=headers)
    assert r.status_code == 200 and r.json()["activo"] is False
    assert _activo_en_base(a["id"]) is False
    # Sigue en la plantilla (como inactivo): no se borra.
    assert [f["activo"] for f in client.get(f"/propiedades/{p}/conceptos", headers=headers).json()] == [False]

    r = client.patch(f"/propiedades/{p}/conceptos/{a['id']}", json={"activo": True}, headers=headers)
    assert r.status_code == 200 and r.json()["activo"] is True
    assert _activo_en_base(a["id"]) is True


def test_patch_con_id_de_otra_propiedad_404_y_no_modifica(client, headers):
    p1, p2, c = _propiedad(), _propiedad(), _concepto()
    a = client.post(f"/propiedades/{p1}/conceptos", json={"concepto_id": c}, headers=headers).json()
    r = client.patch(f"/propiedades/{p2}/conceptos/{a['id']}", json={"activo": False}, headers=headers)
    assert r.status_code == 404 and r.json()["codigo"] == "concepto_propiedad_no_encontrado"
    assert _activo_en_base(a["id"]) is True


def test_patch_inexistente_404(client, headers):
    r = client.patch(f"/propiedades/{_propiedad()}/conceptos/{uuid.uuid4()}",
                     json={"activo": False}, headers=headers)
    assert r.status_code == 404


def test_patch_sin_activo_422(client, headers):
    p, c = _propiedad(), _concepto()
    a = client.post(f"/propiedades/{p}/conceptos", json={"concepto_id": c}, headers=headers).json()
    r = client.patch(f"/propiedades/{p}/conceptos/{a['id']}", json={}, headers=headers)
    assert r.status_code == 422 and r.json()["codigo"] == "validacion"