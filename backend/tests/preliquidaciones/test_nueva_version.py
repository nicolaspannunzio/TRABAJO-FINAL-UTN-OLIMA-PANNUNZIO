"""B9 / HU-14: generar una nueva versión e inmutabilidad (RN-22, RN-23).

Criterio 1: con la versión 1 generada, generar otra vez crea la versión 2 con el importe
corregido y la vigente pasa a ser la 2.
Criterio 2: después de generar la 2, la versión 1 (cabecera, detalle, advertencias y
reparto) es idéntica a la que había antes.
RN-23: la base rechaza UPDATE, DELETE y TRUNCATE sobre las 4 tablas del snapshot.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.core.db import get_engine

SEP, AGO = date(2026, 9, 1), date(2026, 8, 1)
PERIODO = "2026-09-01"
TABLAS_SNAPSHOT = ["preliquidacion", "preliquidacion_detalle", "preliquidacion_advertencia", "reparto"]


@pytest.fixture
def escenario(crear_usuario, make_token, auth, monkeypatch):
    """Propiedad con 2 conceptos cargados en septiembre y 2 propietarios al 50/50.

    - Expensas: $86.200 en septiembre y $60.000 en agosto (variación inusual).
    - TGI: $1.000 en septiembre, sin agosto (sin referencia).
    Así la versión tiene filas en las 4 tablas del snapshot.

    Las tablas del snapshot son inmutables (triggers). Para limpiar, el cierre usa
    session_replication_role = replica, que apaga los triggers SOLO en esa conexión
    de la base de pruebas.
    """
    monkeypatch.setattr(get_settings(), "umbral_variacion_default_pct", Decimal("30.00"))
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    with get_engine().begin() as conn:
        prop = conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                            {"d": f"Calle de prueba {sufijo}"}).scalar_one()
        cps, conceptos, importes, propietarios = [], [], {}, []
        for nombre, sep, ago in [("Expensas", "86200.00", "60000.00"), ("TGI", "1000.00", None)]:
            concepto = conn.execute(text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                                    {"n": f"{nombre} {sufijo}"}).scalar_one()
            cp = conn.execute(text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                                      VALUES (:p, :c) RETURNING id"""),
                              {"p": prop, "c": concepto}).scalar_one()
            conn.execute(text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado)
                                 VALUES (:p, :per, :cp, 'cargado')"""),
                         {"p": prop, "per": SEP, "cp": cp})
            importes[nombre] = conn.execute(
                text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                        VALUES (:cp, :per, :imp, :u) RETURNING id"""),
                {"cp": cp, "per": SEP, "imp": sep, "u": uid}).scalar_one()
            if ago is not None:
                conn.execute(text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                                     VALUES (:cp, :per, :imp, :u)"""),
                             {"cp": cp, "per": AGO, "imp": ago, "u": uid})
            conceptos.append(concepto)
            cps.append(cp)
        for i in range(2):
            propietario = conn.execute(text("INSERT INTO propietario (nombre) VALUES (:n) RETURNING id"),
                                       {"n": f"Propietario {i} {sufijo}"}).scalar_one()
            conn.execute(text("""INSERT INTO propiedad_propietario (propiedad_id, propietario_id, porcentaje)
                                 VALUES (:p, :o, 50)"""), {"p": prop, "o": propietario})
            propietarios.append(propietario)

    yield {"headers": auth(make_token(uid)), "propiedad_id": str(prop),
           "importe_expensas": str(importes["Expensas"])}

    with get_engine().begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        ids = conn.execute(text("SELECT id FROM preliquidacion WHERE propiedad_id = :p"),
                           {"p": prop}).scalars().all()
        for tabla in ("reparto", "preliquidacion_advertencia", "preliquidacion_detalle"):
            conn.execute(text(f"DELETE FROM {tabla} WHERE preliquidacion_id = ANY(:ids)"), {"ids": ids})
        conn.execute(text("DELETE FROM preliquidacion WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                     {"ids": cps})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM propiedad_propietario WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": conceptos})
        conn.execute(text("DELETE FROM propietario WHERE id = ANY(:ids)"), {"ids": propietarios})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop})


def _generar(client, esc):
    r = client.post("/preliquidaciones", headers=esc["headers"],
                    json={"propiedad_id": esc["propiedad_id"], "periodo": PERIODO})
    assert r.status_code == 201, r.text
    return r.json()


def _corregir_expensas(client, esc, importe):
    r = client.patch(f"/importes/{esc['importe_expensas']}", headers=esc["headers"],
                     json={"importe": importe})
    assert r.status_code == 200, r.text


def _filas_del_snapshot(preliquidacion_id):
    """Todas las filas de la versión en las 4 tablas, tal cual están en la base (con sus ids)."""
    with get_engine().connect() as conn:
        filas = {"preliquidacion": conn.execute(
            text("SELECT * FROM preliquidacion WHERE id = :id"), {"id": preliquidacion_id}
        ).mappings().all()}
        for tabla in TABLAS_SNAPSHOT[1:]:
            filas[tabla] = conn.execute(
                text(f"SELECT * FROM {tabla} WHERE preliquidacion_id = :id ORDER BY id"),
                {"id": preliquidacion_id}).mappings().all()
    return {t: [dict(f) for f in fs] for t, fs in filas.items()}


# --- Criterio 1: la versión 2 usa el importe corregido y pasa a ser la vigente -----

def test_regenerar_crea_la_version_2_con_el_importe_corregido_y_es_la_vigente(client, escenario):
    v1 = _generar(client, escenario)
    _corregir_expensas(client, escenario, "68200.00")

    v2 = _generar(client, escenario)

    assert (v1["version"], v2["version"]) == (1, 2)
    assert v1["importe_total"] == "87200.00"
    assert v2["importe_total"] == "69200.00"
    assert sorted(d["importe"] for d in v2["detalle"]) == ["1000.00", "68200.00"]

    vigente = client.get("/preliquidaciones/vigente", headers=escenario["headers"],
                         params={"propiedad_id": escenario["propiedad_id"], "periodo": PERIODO})
    assert vigente.status_code == 200, vigente.text
    assert vigente.json()["id"] == v2["id"]


# --- Criterio 2: la versión 1 queda idéntica ------------------------------------

def test_la_version_1_queda_identica_despues_de_generar_la_2(client, escenario):
    v1 = _generar(client, escenario)
    antes_api = client.get(f"/preliquidaciones/{v1['id']}", headers=escenario["headers"]).json()
    antes_base = _filas_del_snapshot(v1["id"])
    assert all(antes_base[t] for t in TABLAS_SNAPSHOT)  # hay filas en las 4 tablas

    _corregir_expensas(client, escenario, "68200.00")
    _generar(client, escenario)

    despues_api = client.get(f"/preliquidaciones/{v1['id']}", headers=escenario["headers"]).json()
    # Comparación profunda: lo que muestra la API y cada fila de la base, campo por campo.
    assert despues_api == antes_api == v1
    assert _filas_del_snapshot(v1["id"]) == antes_base


# --- RN-23: la base rechaza modificar el snapshot ------------------------------

def _sentencias(preliquidacion_id):
    """Una sentencia prohibida de cada tipo para cada tabla del snapshot."""
    casos = []
    for tabla in TABLAS_SNAPSHOT:
        filtro = "id" if tabla == "preliquidacion" else "preliquidacion_id"
        casos.append((tabla, "UPDATE", f"UPDATE {tabla} SET id = id WHERE {filtro} = :id"))
        casos.append((tabla, "DELETE", f"DELETE FROM {tabla} WHERE {filtro} = :id"))
        # preliquidacion es referenciada por las otras 3: sin CASCADE, PostgreSQL rechaza el
        # TRUNCATE por la clave foránea antes de llegar al trigger. Con CASCADE se prueba el trigger.
        cascade = " CASCADE" if tabla == "preliquidacion" else ""
        casos.append((tabla, "TRUNCATE", f"TRUNCATE {tabla}{cascade}"))
    return casos


@pytest.mark.parametrize(("tabla", "operacion", "indice"),
                         [(t, op, i) for i, (t, op, _) in enumerate(_sentencias(None))])
def test_la_base_rechaza_modificar_el_snapshot(client, escenario, tabla, operacion, indice):
    v1 = _generar(client, escenario)
    _, _, sentencia = _sentencias(v1["id"])[indice]

    with get_engine().connect() as conn:
        transaccion = conn.begin()
        try:
            with pytest.raises(DBAPIError, match="inmutable") as error:
                conn.execute(text(sentencia), {"id": v1["id"]})
            # restrict_violation: el código que lanza bloquear_modificacion_snapshot()
            assert error.value.orig.sqlstate == "23001"
        finally:
            transaccion.rollback()

    assert _filas_del_snapshot(v1["id"])[tabla]  # la versión sigue intacta
