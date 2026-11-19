"""B8 / HU-13: corregir un importe ya preliquidado (RN-14, RN-24).

Criterio 1: el importe queda corregido y `auditoria` guarda el valor anterior, el usuario y la fecha.
Criterio 2: la versión 1 generada antes de corregir sigue mostrando el valor original.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import get_engine
from app.modules.preliquidaciones.service import obtener

SEP = date(2026, 9, 1)
PERIODO = "2026-09-01"


@pytest.fixture
def escenario(crear_usuario, make_token, auth):
    """Propiedad con un concepto cargado en $86.200 y dos propietarios al 50/50.

    Las tablas de la preliquidación son inmutables (triggers). Para limpiar, el cierre
    usa session_replication_role = replica, que apaga los triggers SOLO en esa conexión
    de la base de pruebas.
    """
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    with get_engine().begin() as conn:
        prop = conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                            {"d": f"Calle de prueba {sufijo}"}).scalar_one()
        concepto = conn.execute(text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                                {"n": f"Expensas {sufijo}"}).scalar_one()
        cp = conn.execute(text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                                  VALUES (:p, :c) RETURNING id"""),
                          {"p": prop, "c": concepto}).scalar_one()
        conn.execute(text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado)
                             VALUES (:p, :per, :cp, 'cargado')"""),
                     {"p": prop, "per": SEP, "cp": cp})
        importe_id = conn.execute(
            text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                    VALUES (:cp, :per, 86200.00, :u) RETURNING id"""),
            {"cp": cp, "per": SEP, "u": uid}).scalar_one()
        propietarios = []
        for i in range(2):
            propietario = conn.execute(text("INSERT INTO propietario (nombre) VALUES (:n) RETURNING id"),
                                       {"n": f"Propietario {i} {sufijo}"}).scalar_one()
            conn.execute(text("""INSERT INTO propiedad_propietario (propiedad_id, propietario_id, porcentaje)
                                 VALUES (:p, :o, 50)"""), {"p": prop, "o": propietario})
            propietarios.append(propietario)

    yield {"uid": uid, "headers": auth(make_token(uid)), "propiedad_id": str(prop),
           "cp": str(cp), "importe_id": str(importe_id)}

    with get_engine().begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        ids = conn.execute(text("SELECT id FROM preliquidacion WHERE propiedad_id = :p"),
                           {"p": prop}).scalars().all()
        for tabla in ("reparto", "preliquidacion_advertencia", "preliquidacion_detalle"):
            conn.execute(text(f"DELETE FROM {tabla} WHERE preliquidacion_id = ANY(:ids)"), {"ids": ids})
        conn.execute(text("DELETE FROM preliquidacion WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = :cp"), {"cp": cp})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM propiedad_propietario WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM concepto WHERE id = :c"), {"c": concepto})
        conn.execute(text("DELETE FROM propietario WHERE id = ANY(:ids)"), {"ids": propietarios})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop})


def _corregir(client, esc, importe, importe_id=None):
    return client.patch(f"/importes/{importe_id or esc['importe_id']}", headers=esc["headers"],
                        json={"importe": importe})


def _importe_en_base(importe_id):
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT importe, cargado_por FROM importe_mensual WHERE id = :id"),
                            {"id": importe_id}).mappings().one()


def _auditoria(importe_id):
    with get_engine().connect() as conn:
        return conn.execute(text("""SELECT usuario_id, accion, detalle, fecha FROM auditoria
                                    WHERE entidad = 'importe_mensual' AND entidad_id = :id
                                      AND accion = 'corregir_importe'"""),
                            {"id": importe_id}).mappings().all()


# --- Criterio 1: queda corregido y se audita el valor anterior ----------------

def test_corregir_actualiza_el_importe_y_audita_el_valor_anterior(client, escenario):
    r = _corregir(client, escenario, "68200.00")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == escenario["importe_id"]
    assert body["importe"] == "68200.00"
    assert body["concepto_propiedad_id"] == escenario["cp"]
    assert body["periodo"] == PERIODO

    assert str(_importe_en_base(escenario["importe_id"])["importe"]) == "68200.00"
    [registro] = _auditoria(escenario["importe_id"])
    assert registro["usuario_id"] == escenario["uid"]
    assert registro["fecha"] is not None
    assert registro["detalle"]["importe_anterior"] == "86200.00"
    assert registro["detalle"]["importe_nuevo"] == "68200.00"


# --- Criterio 2: la versión 1 no cambia ---------------------------------------

def test_la_version_1_sigue_mostrando_el_importe_original(client, escenario):
    v1 = client.post("/preliquidaciones", headers=escenario["headers"],
                     json={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})
    assert v1.status_code == 201, v1.text

    assert _corregir(client, escenario, "68200.00").status_code == 200

    with Session(get_engine()) as sesion:
        v1_despues = obtener(sesion, uuid.UUID(v1.json()["id"])).model_dump(mode="json")
    assert v1_despues == v1.json()
    assert [d["importe"] for d in v1_despues["detalle"]] == ["86200.00"]
    assert v1_despues["importe_total"] == "86200.00"


# --- Otros casos ---------------------------------------------------------------

def test_el_checklist_muestra_el_importe_corregido(client, escenario):
    _corregir(client, escenario, "68200.00")

    r = client.get("/checklist", headers=escenario["headers"],
                   params={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})

    [fila] = r.json()["filas"]
    assert fila["estado"] == "cargado"
    assert fila["importe"] == "68200.00"


@pytest.mark.parametrize("importe", ["-2000.00", "0.00"])
def test_se_puede_corregir_a_negativo_o_cero(client, escenario, importe):
    r = _corregir(client, escenario, importe)

    assert r.status_code == 200, r.text
    assert r.json()["importe"] == importe


def test_quien_cargo_no_cambia(client, escenario, crear_usuario, make_token, auth):
    """`cargado_por` sigue siendo quien cargó; quién corrigió queda en la auditoría."""
    otro = crear_usuario("operador")
    esc_otro = {**escenario, "headers": auth(make_token(otro))}

    r = _corregir(client, esc_otro, "68200.00")

    assert r.json()["cargado_por"] == str(escenario["uid"])
    assert _importe_en_base(escenario["importe_id"])["cargado_por"] == escenario["uid"]
    [registro] = _auditoria(escenario["importe_id"])
    assert registro["usuario_id"] == otro


def test_corregir_al_mismo_valor_no_cambia_nada_ni_audita(client, escenario):
    r = _corregir(client, escenario, "86200.00")

    assert r.status_code == 200, r.text
    assert r.json()["importe"] == "86200.00"
    assert _auditoria(escenario["importe_id"]) == []


def test_importe_inexistente_devuelve_404(client, escenario):
    r = _corregir(client, escenario, "100.00", importe_id=uuid.uuid4())

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "importe_no_encontrado"


def test_importe_como_numero_se_rechaza_con_422(client, escenario):
    r = _corregir(client, escenario, 68200.5)

    assert r.status_code == 422, r.text
    assert r.json()["codigo"] == "validacion"
    assert str(_importe_en_base(escenario["importe_id"])["importe"]) == "86200.00"


def test_si_falla_la_auditoria_el_importe_no_cambia(escenario, monkeypatch):
    """Una sola transacción: sin auditoría no hay corrección."""
    from fastapi.testclient import TestClient

    from app import audit
    from app.main import app as fastapi_app

    def _falla(*args, **kwargs):
        raise RuntimeError("auditoría caída")

    monkeypatch.setattr(audit, "registrar", _falla)

    # raise_server_exceptions=False: queremos ver el 500 que arma el handler, no la excepción.
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        r = _corregir(c, escenario, "68200.00")

    assert r.status_code == 500, r.text
    assert str(_importe_en_base(escenario["importe_id"])["importe"]) == "86200.00"
