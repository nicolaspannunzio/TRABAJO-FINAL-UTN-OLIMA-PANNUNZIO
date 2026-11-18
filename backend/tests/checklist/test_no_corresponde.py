"""B3 / HU-09: marcar un concepto como no corresponde (RN-10, RN-24, RN-25).

Criterios 1, 2 y 3 de HU-09 contra la API y la base. El criterio 5 (confirmación en la
pantalla) es del frontend y se verifica a mano. El criterio 4 (versiones 1 y 2 de la
preliquidación) se cierra cuando B6 esté mergeado.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.core.db import get_engine

PERIODO = "2026-09-01"


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def escenario(crear_usuario, make_token, auth):
    """Operador + propiedad con el período 2026-09 abierto (3 conceptos, todos pendiente).

    Pide crear_usuario primero para que su limpieza corra DESPUÉS de la de este fixture
    (importe_mensual.cargado_por apunta a usuario).
    """
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    cps, concepto_ids = [], []

    with get_engine().begin() as conn:
        prop_id = conn.execute(
            text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
            {"d": f"Calle de prueba {sufijo}"},
        ).scalar_one()
        for i in range(3):
            concepto_id = conn.execute(
                text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                {"n": f"Concepto {i} {sufijo}"},
            ).scalar_one()
            concepto_ids.append(concepto_id)
            cp_id = conn.execute(
                text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                        VALUES (:p, :c) RETURNING id"""),
                {"p": prop_id, "c": concepto_id},
            ).scalar_one()
            cps.append(cp_id)

    headers = auth(make_token(uid))
    yield {"uid": uid, "headers": headers, "propiedad_id": str(prop_id),
           "cps": [str(c) for c in cps]}

    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                     {"ids": cps})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": concepto_ids})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop_id})


@pytest.fixture
def abierto(client, escenario):
    """Abre el período por la API (B1) y devuelve {concepto_propiedad_id: fila_id}."""
    r = client.post("/checklist", headers=escenario["headers"],
                    json={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})
    assert r.status_code == 201, r.text
    return {f["concepto_propiedad_id"]: f["id"] for f in r.json()["filas"]}


def _cargar(client, esc, cp_id, importe):
    r = client.post("/importes", headers=esc["headers"], json={
        "propiedad_id": esc["propiedad_id"], "periodo": PERIODO,
        "concepto_propiedad_id": cp_id, "importe": importe,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _marcar(client, esc, fila_id):
    return client.post(f"/checklist/{fila_id}/no-corresponde", headers=esc["headers"])


def _estado(fila_id):
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT estado FROM checklist_periodo WHERE id = :id"),
                            {"id": fila_id}).scalar_one()


def _importes(cp_id):
    with get_engine().connect() as conn:
        return conn.execute(
            text("SELECT id, importe FROM importe_mensual WHERE concepto_propiedad_id = :cp"),
            {"cp": cp_id},
        ).mappings().all()


def _auditoria(fila_id):
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT usuario_id, accion, detalle, fecha FROM auditoria
                    WHERE entidad = 'checklist_periodo' AND entidad_id = :id"""),
            {"id": fila_id},
        ).mappings().all()


# --- Criterio 1: pendiente → no_corresponde, sin importe ---------------------

def test_marcar_pendiente_pasa_a_no_corresponde_sin_importe(client, escenario, abierto):
    cp = escenario["cps"][0]
    fila_id = abierto[cp]

    r = _marcar(client, escenario, fila_id)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == fila_id
    assert body["estado"] == "no_corresponde"
    assert body["estado_anterior"] == "pendiente"
    assert body["importe"] is None and body["importe_id"] is None
    assert body["importe_eliminado"] is None
    assert _estado(fila_id) == "no_corresponde"

    [registro] = _auditoria(fila_id)
    assert registro["usuario_id"] == escenario["uid"]
    assert registro["accion"] == "marcar_no_corresponde"
    assert registro["detalle"]["estado_anterior"] == "pendiente"
    assert registro["detalle"]["importe_anterior"] is None


# --- Criterio 2: $0 y no_corresponde son estados distintos -------------------

def test_cero_y_no_corresponde_se_muestran_distintos(client, escenario, abierto):
    cp_cero, cp_nc = escenario["cps"][0], escenario["cps"][1]
    _cargar(client, escenario, cp_cero, "0.00")
    _marcar(client, escenario, abierto[cp_nc])

    r = client.get("/checklist", headers=escenario["headers"],
                   params={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})

    assert r.status_code == 200, r.text
    filas = {f["concepto_propiedad_id"]: f for f in r.json()["filas"]}
    assert filas[cp_cero]["estado"] == "cargado"
    assert filas[cp_cero]["importe"] == "0.00"
    assert filas[cp_nc]["estado"] == "no_corresponde"
    assert filas[cp_nc]["importe"] is None


# --- Criterio 3: cargado → se borra el importe y se audita el anterior -------

def test_marcar_cargado_borra_el_importe_y_audita_el_valor_anterior(client, escenario, abierto):
    cp = escenario["cps"][0]
    fila_id = abierto[cp]
    cargada = _cargar(client, escenario, cp, "86200.00")

    r = _marcar(client, escenario, fila_id)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estado"] == "no_corresponde"
    assert body["estado_anterior"] == "cargado"
    assert body["importe_eliminado"] == "86200.00"
    assert body["importe"] is None and body["importe_id"] is None

    assert _importes(cp) == []
    assert _estado(fila_id) == "no_corresponde"

    [registro] = _auditoria(fila_id)
    assert registro["usuario_id"] == escenario["uid"]
    assert registro["fecha"] is not None
    anterior = registro["detalle"]["importe_anterior"]
    assert anterior["id"] == cargada["importe_id"]
    assert anterior["importe"] == "86200.00"
    assert anterior["cargado_por"] == str(escenario["uid"])
    assert anterior["fecha_carga"]  # fecha de la carga original, como texto


# --- Idempotencia, 404 y atomicidad ------------------------------------------

def test_marcar_dos_veces_es_idempotente_y_no_audita_de_nuevo(client, escenario, abierto):
    fila_id = abierto[escenario["cps"][0]]
    _marcar(client, escenario, fila_id)

    r = _marcar(client, escenario, fila_id)

    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "no_corresponde"
    assert r.json()["estado_anterior"] == "no_corresponde"
    assert len(_auditoria(fila_id)) == 1  # solo la primera marca


def test_fila_inexistente_devuelve_404(client, escenario):
    r = _marcar(client, escenario, uuid.uuid4())

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "fila_no_encontrada"


def test_si_falla_la_auditoria_no_se_borra_el_importe(escenario, abierto, client, monkeypatch):
    """Una sola transacción: sin auditoría el importe sigue y la fila sigue cargado."""
    from fastapi.testclient import TestClient

    from app import audit
    from app.main import app as fastapi_app

    cp = escenario["cps"][0]
    fila_id = abierto[cp]
    _cargar(client, escenario, cp, "15000.00")

    def _falla(*args, **kwargs):
        raise RuntimeError("auditoría caída")

    monkeypatch.setattr(audit, "registrar", _falla)

    # raise_server_exceptions=False: queremos ver el 500 que arma el handler, no la excepción.
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        r = _marcar(c, escenario, fila_id)

    assert r.status_code == 500, r.text
    assert [str(i["importe"]) for i in _importes(cp)] == ["15000.00"]
    assert _estado(fila_id) == "cargado"
