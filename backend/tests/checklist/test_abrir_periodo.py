"""B1 / HU-07: apertura de período y checklist (RN-01, RN-09, RN-10).

Cada test arma sus propios datos (una propiedad con 4 conceptos activos y 1 inactivo
en su plantilla) y los borra al terminar. No depende de la semilla: la semilla se usa
en la verificación manual del "Done cuando".
"""
import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.core.db import get_engine

PERIODO = "2026-09-01"


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def operador(crear_usuario, make_token, auth):
    """Headers de un operador activo (B1 no exige rol admin)."""
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture
def propiedad_con_plantilla():
    """Propiedad con 4 conceptos activos y 1 inactivo en su plantilla (criterio 1 de HU-07)."""
    sufijo = uuid.uuid4().hex[:8]  # concepto.nombre es UNIQUE y la base se comparte en la corrida
    activos, inactivos, concepto_ids = set(), set(), []

    with get_engine().begin() as conn:
        prop_id = conn.execute(
            text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
            {"d": f"Calle de prueba {sufijo}"},
        ).scalar_one()

        for i, activo in enumerate([True, True, True, True, False]):
            concepto_id = conn.execute(
                text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                {"n": f"Concepto {i} {sufijo}"},
            ).scalar_one()
            concepto_ids.append(concepto_id)
            cp_id = conn.execute(
                text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id, activo)
                        VALUES (:p, :c, :a) RETURNING id"""),
                {"p": prop_id, "c": concepto_id, "a": activo},
            ).scalar_one()
            (activos if activo else inactivos).add(str(cp_id))

    yield {"id": str(prop_id), "activos": activos, "inactivos": inactivos}

    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": concepto_ids})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop_id})


def _filas_en_base(propiedad_id: str):
    """Lo que realmente quedó en checklist_periodo, sin pasar por la API."""
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT id, concepto_propiedad_id, periodo, estado
                    FROM checklist_periodo WHERE propiedad_id = :p"""),
            {"p": propiedad_id},
        ).mappings().all()


def _abrir(client, headers, propiedad_id, periodo=PERIODO):
    return client.post("/checklist", json={"propiedad_id": propiedad_id, "periodo": periodo},
                       headers=headers)


# --- Criterio 1: una fila pendiente por concepto activo ----------------------

def test_abrir_crea_una_fila_pendiente_por_concepto_activo(client, operador,
                                                          propiedad_con_plantilla):
    prop = propiedad_con_plantilla

    r = _abrir(client, operador, prop["id"])

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["propiedad_id"] == prop["id"]
    assert body["periodo"] == PERIODO

    filas = body["filas"]
    assert len(filas) == 4
    assert {f["concepto_propiedad_id"] for f in filas} == prop["activos"]
    assert not {f["concepto_propiedad_id"] for f in filas} & prop["inactivos"]
    for f in filas:
        assert f["estado"] == "pendiente"
        assert f["importe"] is None and f["importe_id"] is None
        assert f["concepto"].startswith("Concepto ")  # nombre leído de `concepto`

    en_base = _filas_en_base(prop["id"])
    assert len(en_base) == 4
    assert {str(f["concepto_propiedad_id"]) for f in en_base} == prop["activos"]
    assert all(f["periodo"] == date(2026, 9, 1) for f in en_base)
    assert all(f["estado"] == "pendiente" for f in en_base)


# --- Criterio 2: período que no es el primer día del mes ---------------------

def test_periodo_que_no_es_primer_dia_se_rechaza_con_422_sin_crear_filas(
        client, operador, propiedad_con_plantilla):
    prop = propiedad_con_plantilla

    r = _abrir(client, operador, prop["id"], periodo="2026-09-15")

    assert r.status_code == 422, r.text
    body = r.json()
    assert body["codigo"] == "validacion"
    assert set(body) == {"codigo", "mensaje", "detalle"}
    # Nunca normaliza: no queda ninguna fila, ni del 15 ni del 1.
    assert _filas_en_base(prop["id"]) == []


# --- Criterio 3: abrir dos veces no duplica ----------------------------------

def test_abrir_dos_veces_no_duplica_filas(client, operador, propiedad_con_plantilla):
    prop = propiedad_con_plantilla

    r1 = _abrir(client, operador, prop["id"])
    r2 = _abrir(client, operador, prop["id"])

    assert r1.status_code == 201, r1.text
    assert r2.status_code == 200, r2.text  # el existente, sin error
    ids1 = {f["id"] for f in r1.json()["filas"]}
    ids2 = {f["id"] for f in r2.json()["filas"]}
    assert ids1 == ids2
    assert len(_filas_en_base(prop["id"])) == 4


# --- Contrato: 404 y GET /checklist ------------------------------------------

def test_abrir_propiedad_inexistente_devuelve_404(client, operador):
    r = _abrir(client, operador, str(uuid.uuid4()))

    assert r.status_code == 404, r.text
    assert set(r.json()) == {"codigo", "mensaje", "detalle"}


def test_get_devuelve_el_checklist_abierto(client, operador, propiedad_con_plantilla):
    prop = propiedad_con_plantilla
    abierto = _abrir(client, operador, prop["id"]).json()

    r = client.get("/checklist", params={"propiedad_id": prop["id"], "periodo": PERIODO},
                   headers=operador)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["propiedad_id"] == prop["id"] and body["periodo"] == PERIODO
    assert {f["id"] for f in body["filas"]} == {f["id"] for f in abierto["filas"]}


def test_get_de_periodo_no_abierto_devuelve_404(client, operador, propiedad_con_plantilla):
    r = client.get("/checklist",
                   params={"propiedad_id": propiedad_con_plantilla["id"], "periodo": PERIODO},
                   headers=operador)

    assert r.status_code == 404, r.text
