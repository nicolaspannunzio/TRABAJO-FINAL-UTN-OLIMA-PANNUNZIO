"""B2 / HU-08: carga de importes (RN-10, RN-11, RN-12, RN-13, RN-24).

Cada test arma sus propios datos: una propiedad con 4 conceptos activos y 1 inactivo,
y el período 2026-09 abierto (filas 'pendiente' de los activos). No depende de la semilla.
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
    """Operador + propiedad con el período abierto.

    Pide crear_usuario primero para que su limpieza corra DESPUÉS de la de este fixture:
    importe_mensual.cargado_por apunta a usuario, así que los importes se borran antes.
    """
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    activos, concepto_ids = [], []

    with get_engine().begin() as conn:
        prop_id = conn.execute(
            text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
            {"d": f"Calle de prueba {sufijo}"},
        ).scalar_one()

        inactivo = None
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
            if activo:
                activos.append(cp_id)
                conn.execute(
                    text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id)
                            VALUES (:p, :per, :cp)"""),
                    {"p": prop_id, "per": date(2026, 9, 1), "cp": cp_id},
                )
            else:
                inactivo = cp_id

    yield {
        "uid": uid,
        "headers": auth(make_token(uid)),
        "propiedad_id": str(prop_id),
        "activos": [str(a) for a in activos],
        "inactivo": str(inactivo),
    }

    with get_engine().begin() as conn:
        cps = activos + [inactivo]
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                     {"ids": cps})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": concepto_ids})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop_id})


def _cargar(client, esc, cp_id, importe, periodo=PERIODO):
    return client.post("/importes", headers=esc["headers"], json={
        "propiedad_id": esc["propiedad_id"], "periodo": periodo,
        "concepto_propiedad_id": cp_id, "importe": importe,
    })


def _importes_en_base(cp_id):
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT id, importe, cargado_por FROM importe_mensual
                    WHERE concepto_propiedad_id = :cp AND periodo = :per"""),
            {"cp": cp_id, "per": date(2026, 9, 1)},
        ).mappings().all()


def _estado_fila(esc, cp_id):
    with get_engine().connect() as conn:
        return conn.execute(
            text("""SELECT estado FROM checklist_periodo
                    WHERE propiedad_id = :p AND periodo = :per AND concepto_propiedad_id = :cp"""),
            {"p": esc["propiedad_id"], "per": date(2026, 9, 1), "cp": cp_id},
        ).scalar_one()


# --- Criterio 1: la fila pasa a cargado y queda auditada ---------------------

def test_cargar_importe_pasa_la_fila_a_cargado_y_audita(client, escenario):
    cp = escenario["activos"][0]

    r = _cargar(client, escenario, cp, "15000.00")

    assert r.status_code == 201, r.text
    fila = r.json()
    assert fila["concepto_propiedad_id"] == cp
    assert fila["estado"] == "cargado"
    assert fila["importe"] == "15000.00"
    assert fila["importe_id"] is not None

    [importe] = _importes_en_base(cp)
    assert str(importe["id"]) == fila["importe_id"]
    assert str(importe["importe"]) == "15000.00"
    assert importe["cargado_por"] == escenario["uid"]
    assert _estado_fila(escenario, cp) == "cargado"

    with get_engine().connect() as conn:
        auditoria = conn.execute(
            text("""SELECT usuario_id, accion, detalle FROM auditoria
                    WHERE entidad = 'importe_mensual' AND entidad_id = :id"""),
            {"id": importe["id"]},
        ).mappings().all()
    assert len(auditoria) == 1
    assert auditoria[0]["usuario_id"] == escenario["uid"]
    assert auditoria[0]["accion"] == "carga_importe"
    assert auditoria[0]["detalle"]["importe"] == "15000.00"
    assert auditoria[0]["detalle"]["estado_anterior"] == "pendiente"


def test_el_checklist_muestra_el_importe_cargado(client, escenario):
    cp = escenario["activos"][0]
    _cargar(client, escenario, cp, "15000.00")

    r = client.get("/checklist", headers=escenario["headers"],
                   params={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})

    assert r.status_code == 200, r.text
    [fila] = [f for f in r.json()["filas"] if f["concepto_propiedad_id"] == cp]
    assert fila["estado"] == "cargado" and fila["importe"] == "15000.00"


# --- Criterio 2: duplicado rechazado, se conserva el primero -----------------

def test_importe_duplicado_se_rechaza_con_409_y_conserva_el_primero(client, escenario):
    cp = escenario["activos"][0]
    primero = _cargar(client, escenario, cp, "15000.00")

    r = _cargar(client, escenario, cp, "99999.00")

    assert primero.status_code == 201
    assert r.status_code == 409, r.text
    body = r.json()
    assert body["codigo"] == "importe_duplicado"
    assert set(body) == {"codigo", "mensaje", "detalle"}

    [importe] = _importes_en_base(cp)
    assert str(importe["importe"]) == "15000.00"
    assert str(importe["id"]) == primero.json()["importe_id"]


# --- Criterio 3: negativos y cero se aceptan ---------------------------------

@pytest.mark.parametrize("importe", ["-2000.00", "0.00"])
def test_importe_negativo_o_cero_se_acepta(client, escenario, importe):
    cp = escenario["activos"][1]

    r = _cargar(client, escenario, cp, importe)

    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "cargado"
    assert r.json()["importe"] == importe
    assert _estado_fila(escenario, cp) == "cargado"


# --- Criterio 4: concepto sin fila en el checklist ---------------------------

def test_concepto_inactivo_sin_fila_se_rechaza(client, escenario):
    r = _cargar(client, escenario, escenario["inactivo"], "500.00")

    assert r.status_code == 422, r.text
    assert r.json()["codigo"] == "concepto_sin_fila_checklist"
    assert _importes_en_base(escenario["inactivo"]) == []


def test_periodo_sin_abrir_se_rechaza(client, escenario):
    cp = escenario["activos"][0]

    r = _cargar(client, escenario, cp, "500.00", periodo="2026-10-01")

    assert r.status_code == 422, r.text
    assert r.json()["codigo"] == "concepto_sin_fila_checklist"
    with get_engine().connect() as conn:
        n = conn.execute(
            text("SELECT count(*) FROM importe_mensual WHERE concepto_propiedad_id = :cp"),
            {"cp": cp},
        ).scalar_one()
    assert n == 0


# --- Contrato y atomicidad ---------------------------------------------------

def test_importe_como_numero_se_rechaza_con_422(client, escenario):
    """El contrato exige cadenas decimales, nunca float."""
    r = _cargar(client, escenario, escenario["activos"][0], 15000.5)

    assert r.status_code == 422, r.text
    assert r.json()["codigo"] == "validacion"


def test_si_falla_la_auditoria_no_queda_nada(escenario, monkeypatch):
    """Una sola transacción: sin auditoría no hay importe ni cambio de estado."""
    from fastapi.testclient import TestClient

    from app import audit
    from app.main import app as fastapi_app

    def _falla(*args, **kwargs):
        raise RuntimeError("auditoría caída")

    monkeypatch.setattr(audit, "registrar", _falla)
    cp = escenario["activos"][0]

    # raise_server_exceptions=False: queremos ver el 500 que arma el handler, no la excepción.
    with TestClient(fastapi_app, raise_server_exceptions=False) as client:
        r = _cargar(client, escenario, cp, "15000.00")

    assert r.status_code == 500, r.text
    assert _importes_en_base(cp) == []
    assert _estado_fila(escenario, cp) == "pendiente"
