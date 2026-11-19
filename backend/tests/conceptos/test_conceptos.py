"""A5 / HU-05: catálogo de conceptos (RN-07).

Cada test crea sus propios datos (prefijo "A5-test") y los borra al terminar:
no depende de la semilla ni deja filas para otros tests.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.db import get_engine

PREFIJO = "A5-test"


@pytest.fixture
def headers(crear_usuario, make_token, auth):
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture(autouse=True)
def limpiar():
    yield
    with get_engine().begin() as conn:
        conn.execute(
            text("DELETE FROM concepto WHERE nombre ILIKE :p"), {"p": f"{PREFIJO}%"}
        )


def _nombre() -> str:
    return f"{PREFIJO} {uuid.uuid4().hex[:8]}"


def _cantidad(nombre: str) -> int:
    with get_engine().connect() as conn:
        return conn.execute(
            text("SELECT count(*) FROM concepto WHERE nombre = :n"), {"n": nombre}
        ).scalar_one()


def _umbral_en_base(concepto_id: str):
    with get_engine().connect() as conn:
        return conn.execute(
            text("SELECT umbral_variacion_pct FROM concepto WHERE id = :i"),
            {"i": concepto_id},
        ).scalar_one()


# --- Criterio 1: nombre repetido -------------------------------------------------


def test_nombre_repetido_se_rechaza_409(client, headers):
    nombre = _nombre()
    assert (
        client.post("/conceptos", json={"nombre": nombre}, headers=headers).status_code
        == 201
    )
    r = client.post(
        "/conceptos", json={"nombre": nombre, "tipo": "otro"}, headers=headers
    )
    assert r.status_code == 409
    assert r.json()["codigo"] == "concepto_duplicado"
    assert _cantidad(nombre) == 1  # conserva el primero


def test_nombre_repetido_con_otras_mayusculas_se_rechaza_409(client, headers):
    nombre = _nombre()
    assert (
        client.post("/conceptos", json={"nombre": nombre}, headers=headers).status_code
        == 201
    )
    for variante in (nombre.upper(), nombre.lower()):
        r = client.post("/conceptos", json={"nombre": variante}, headers=headers)
        assert r.status_code == 409
        assert r.json()["codigo"] == "concepto_duplicado"


def test_editar_con_nombre_de_otro_en_otras_mayusculas_409(client, headers):
    a = client.post("/conceptos", json={"nombre": _nombre()}, headers=headers).json()
    b = client.post("/conceptos", json={"nombre": _nombre()}, headers=headers).json()
    r = client.patch(
        f"/conceptos/{b['id']}", json={"nombre": a["nombre"].upper()}, headers=headers
    )
    assert r.status_code == 409 and r.json()["codigo"] == "concepto_duplicado"


def test_editar_solo_las_mayusculas_de_su_propio_nombre_es_valido(client, headers):
    creado = client.post(
        "/conceptos", json={"nombre": _nombre()}, headers=headers
    ).json()
    r = client.patch(
        f"/conceptos/{creado['id']}",
        json={"nombre": creado["nombre"].upper()},
        headers=headers,
    )
    assert r.status_code == 200


# --- Criterio 2: sin umbral queda NULL ---------------------------------------------


def test_concepto_sin_umbral_queda_null(client, headers):
    r = client.post("/conceptos", json={"nombre": _nombre()}, headers=headers)
    assert r.status_code == 201
    cuerpo = r.json()
    assert (
        cuerpo["umbral_variacion_pct"] is None
        and cuerpo["tipo"] is None
        and cuerpo["id"]
    )
    assert _umbral_en_base(cuerpo["id"]) is None


def test_concepto_con_umbral_propio(client, headers):
    r = client.post(
        "/conceptos",
        json={"nombre": _nombre(), "tipo": "impuesto", "umbral_variacion_pct": "45.5"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["umbral_variacion_pct"] == "45.50"
    assert _umbral_en_base(r.json()["id"]) == Decimal("45.50")


# --- Criterio 3: umbral 0 o negativo -----------------------------------------------


@pytest.mark.parametrize("umbral", ["0", "0.00", "-5", "-0.01", 30, "abc", "1000.00"])
def test_umbral_invalido_se_rechaza_422(client, headers, umbral):
    nombre = _nombre()
    r = client.post(
        "/conceptos",
        json={"nombre": nombre, "umbral_variacion_pct": umbral},
        headers=headers,
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "validacion"
    assert _cantidad(nombre) == 0


# --- Alta: validaciones de texto -----------------------------------------------------


@pytest.mark.parametrize("cuerpo", [{}, {"nombre": ""}, {"nombre": "   "}])
def test_nombre_invalido_422(client, headers, cuerpo):
    r = client.post("/conceptos", json=cuerpo, headers=headers)
    assert r.status_code == 422 and r.json()["codigo"] == "validacion"


def test_espacios_en_los_bordes_se_recortan_y_tipo_vacio_es_null(client, headers):
    nombre = _nombre()
    r = client.post(
        "/conceptos", json={"nombre": f"  {nombre}  ", "tipo": "  "}, headers=headers
    )
    assert r.status_code == 201
    assert r.json()["nombre"] == nombre and r.json()["tipo"] is None


# --- Listado ----------------------------------------------------------------------------


def test_listar_incluye_el_concepto_creado(client, headers):
    creado = client.post(
        "/conceptos", json={"nombre": _nombre()}, headers=headers
    ).json()
    r = client.get("/conceptos", headers=headers)
    assert r.status_code == 200
    assert creado in r.json()


# --- Edición ----------------------------------------------------------------------------


def test_editar_solo_cambia_lo_enviado(client, headers):
    creado = client.post(
        "/conceptos",
        json={"nombre": _nombre(), "tipo": "impuesto", "umbral_variacion_pct": "20"},
        headers=headers,
    ).json()
    r = client.patch(
        f"/conceptos/{creado['id']}", json={"tipo": "servicio"}, headers=headers
    )
    assert r.status_code == 200
    assert r.json()["tipo"] == "servicio"
    assert r.json()["nombre"] == creado["nombre"]
    assert r.json()["umbral_variacion_pct"] == "20.00"


def test_editar_umbral_null_vuelve_al_global(client, headers):
    creado = client.post(
        "/conceptos",
        json={"nombre": _nombre(), "umbral_variacion_pct": "20"},
        headers=headers,
    ).json()
    r = client.patch(
        f"/conceptos/{creado['id']}",
        json={"umbral_variacion_pct": None},
        headers=headers,
    )
    assert r.status_code == 200 and r.json()["umbral_variacion_pct"] is None
    assert _umbral_en_base(creado["id"]) is None


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"umbral_variacion_pct": "0"},
        {"umbral_variacion_pct": "-1"},
        {"nombre": None},
        {"nombre": " "},
    ],
)
def test_editar_invalido_422_y_no_modifica(client, headers, cuerpo):
    creado = client.post(
        "/conceptos",
        json={"nombre": _nombre(), "umbral_variacion_pct": "20"},
        headers=headers,
    ).json()
    r = client.patch(f"/conceptos/{creado['id']}", json=cuerpo, headers=headers)
    assert r.status_code == 422
    assert _umbral_en_base(creado["id"]) == Decimal("20.00")


def test_editar_con_nombre_de_otro_concepto_409(client, headers):
    a = client.post("/conceptos", json={"nombre": _nombre()}, headers=headers).json()
    b = client.post("/conceptos", json={"nombre": _nombre()}, headers=headers).json()
    r = client.patch(
        f"/conceptos/{b['id']}", json={"nombre": a["nombre"]}, headers=headers
    )
    assert r.status_code == 409 and r.json()["codigo"] == "concepto_duplicado"
    assert _cantidad(b["nombre"]) == 1  # b conserva su nombre


def test_editar_conservando_su_propio_nombre_es_valido(client, headers):
    creado = client.post(
        "/conceptos", json={"nombre": _nombre()}, headers=headers
    ).json()
    r = client.patch(
        f"/conceptos/{creado['id']}",
        json={"nombre": creado["nombre"], "tipo": "x"},
        headers=headers,
    )
    assert r.status_code == 200


def test_editar_concepto_inexistente_404(client, headers):
    r = client.patch(f"/conceptos/{uuid.uuid4()}", json={"tipo": "x"}, headers=headers)
    assert r.status_code == 404
    assert r.json()["codigo"] == "concepto_no_encontrado"
