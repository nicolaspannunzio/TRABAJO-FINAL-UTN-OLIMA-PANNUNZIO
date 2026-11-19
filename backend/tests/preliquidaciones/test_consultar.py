"""B7 / HU-12: consultar preliquidaciones (RN-21, RN-22).

Criterio 1: con versiones 1 y 2, la vigente es la 2.
Criterio 2: la versión 1 se ve tal como se generó, sin depender de `auditoria` ni de los
importes actuales.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.core.db import get_engine

SEP = date(2026, 9, 1)
PERIODO = "2026-09-01"


@pytest.fixture
def escenario(crear_usuario, make_token, auth):
    """Propiedad con 2 conceptos cargados en septiembre y 2 propietarios al 50/50.

    Las tablas de la preliquidación son inmutables (triggers). Para limpiar, el cierre
    usa session_replication_role = replica, que apaga los triggers SOLO en esa conexión
    de la base de pruebas.
    """
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    with get_engine().begin() as conn:
        prop = conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                            {"d": f"Calle de prueba {sufijo}"}).scalar_one()
        cps, conceptos, propietarios = [], [], []
        for i, importe in enumerate(["86200.00", "1000.00"]):
            concepto = conn.execute(text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                                    {"n": f"C{i} {sufijo}"}).scalar_one()
            cp = conn.execute(text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                                      VALUES (:p, :c) RETURNING id"""),
                              {"p": prop, "c": concepto}).scalar_one()
            conn.execute(text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado)
                                 VALUES (:p, :per, :cp, 'cargado')"""),
                         {"p": prop, "per": SEP, "cp": cp})
            conn.execute(text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                                 VALUES (:cp, :per, :imp, :u)"""),
                         {"cp": cp, "per": SEP, "imp": importe, "u": uid})
            conceptos.append(concepto)
            cps.append(cp)
        for i in range(2):
            propietario = conn.execute(
                text("INSERT INTO propietario (nombre) VALUES (:n) RETURNING id"),
                {"n": f"Propietario {i} {sufijo}"}).scalar_one()
            conn.execute(text("""INSERT INTO propiedad_propietario (propiedad_id, propietario_id, porcentaje)
                                 VALUES (:p, :o, 50)"""), {"p": prop, "o": propietario})
            propietarios.append(propietario)

    yield {"headers": auth(make_token(uid)), "propiedad_id": str(prop), "cps": cps}

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


def _params(esc, periodo=PERIODO):
    return {"propiedad_id": esc["propiedad_id"], "periodo": periodo}


def _cambiar_importe_en_la_base(cp, importe):
    """Simula una corrección posterior (HU-13) tocando importe_mensual directamente."""
    with get_engine().begin() as conn:
        conn.execute(text("UPDATE importe_mensual SET importe = :i WHERE concepto_propiedad_id = :cp"),
                     {"i": importe, "cp": cp})


# --- Criterio 1: la vigente es la de mayor versión -----------------------------

def test_con_versiones_1_y_2_la_vigente_es_la_2(client, escenario):
    _generar(client, escenario)
    _cambiar_importe_en_la_base(escenario["cps"][0], "68200.00")
    v2 = _generar(client, escenario)

    r = client.get("/preliquidaciones/vigente", headers=escenario["headers"], params=_params(escenario))

    assert r.status_code == 200, r.text
    assert r.json() == v2
    assert r.json()["version"] == 2
    assert r.json()["importe_total"] == "69200.00"


def test_el_listado_trae_todas_las_versiones_en_orden(client, escenario):
    v1 = _generar(client, escenario)
    v2 = _generar(client, escenario)

    r = client.get("/preliquidaciones", headers=escenario["headers"], params=_params(escenario))

    assert r.status_code == 200, r.text
    assert [v["version"] for v in r.json()] == [1, 2]
    assert [v["id"] for v in r.json()] == [v1["id"], v2["id"]]
    # El listado trae solo la cabecera, sin detalle ni reparto.
    assert "detalle" not in r.json()[0]


# --- Criterio 2: la versión 1 tal como se generó, sin depender de auditoria ------

def test_la_version_1_se_ve_como_se_genero_sin_depender_de_auditoria(client, escenario):
    v1 = _generar(client, escenario)
    assert v1["importe_total"] == "87200.00"

    # Después de generar: cambia el importe y se borra toda la auditoría de la versión.
    _cambiar_importe_en_la_base(escenario["cps"][0], "68200.00")
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM auditoria WHERE entidad_id = :id"), {"id": v1["id"]})

    r = client.get(f"/preliquidaciones/{v1['id']}", headers=escenario["headers"])

    assert r.status_code == 200, r.text
    assert r.json() == v1  # cabecera, detalle, advertencias y reparto idénticos
    assert sorted(d["importe"] for d in r.json()["detalle"]) == ["1000.00", "86200.00"]
    assert [x["importe_correspondiente"] for x in r.json()["reparto"]] == ["43600.00", "43600.00"]


# --- 404 y casos vacíos --------------------------------------------------------

def test_sin_versiones_el_listado_es_vacio_y_la_vigente_404(client, escenario):
    lista = client.get("/preliquidaciones", headers=escenario["headers"], params=_params(escenario))
    vigente = client.get("/preliquidaciones/vigente", headers=escenario["headers"],
                         params=_params(escenario))

    assert lista.status_code == 200 and lista.json() == []
    assert vigente.status_code == 404, vigente.text
    assert vigente.json()["codigo"] == "preliquidacion_no_encontrada"


def test_version_inexistente_devuelve_404(client, escenario):
    r = client.get(f"/preliquidaciones/{uuid.uuid4()}", headers=escenario["headers"])

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "preliquidacion_no_encontrada"


def test_listado_de_propiedad_inexistente_devuelve_404(client, escenario):
    r = client.get("/preliquidaciones", headers=escenario["headers"],
                   params={"propiedad_id": str(uuid.uuid4()), "periodo": PERIODO})

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "propiedad_no_encontrada"


def test_vigente_no_se_confunde_con_un_id(client, escenario):
    """La ruta /vigente está declarada antes que /{id}: no responde 422 por id inválido."""
    _generar(client, escenario)

    r = client.get("/preliquidaciones/vigente", headers=escenario["headers"], params=_params(escenario))

    assert r.status_code == 200, r.text
