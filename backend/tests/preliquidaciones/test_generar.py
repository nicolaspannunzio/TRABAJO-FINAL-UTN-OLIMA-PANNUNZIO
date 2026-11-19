"""B6 / HU-11: generar la preliquidación (RN-17 a RN-22, RN-24).

También cierra dos criterios que quedaron esperando a B6:
- HU-10, criterio 5: las advertencias no impiden generar.
- HU-09, criterio 4: marcar no corresponde y generar la versión 2 no cambia la versión 1.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import get_engine
from app.modules.preliquidaciones.service import obtener

SEP, AGO = date(2026, 9, 1), date(2026, 8, 1)
PERIODO = "2026-09-01"

# ids de propietarios fijos y ordenados: el reparto se ordena por id (RN-21).
PROPIETARIOS = [uuid.UUID(f"00000000-0000-4000-8000-0000000000{n:02d}") for n in (1, 2, 3)]


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def armar(crear_usuario, make_token, auth, monkeypatch):
    """Arma una propiedad con conceptos, checklist de septiembre y propietarios.

    armar(conceptos=[(estado, importe_sep, importe_ago)], reparto=[porcentajes])
    Devuelve headers, propiedad_id y los concepto_propiedad_id en el mismo orden.

    Las tablas de la preliquidación son inmutables (triggers). Para limpiar, el cierre
    usa session_replication_role = replica, que apaga los triggers SOLO en esa conexión
    de la base de pruebas. Nunca se hace algo así fuera de los tests.
    """
    monkeypatch.setattr(get_settings(), "umbral_variacion_default_pct", Decimal("30.00"))
    uid = crear_usuario("operador")
    creadas: list[uuid.UUID] = []
    propietarios_creados: set[uuid.UUID] = set()

    def _armar(conceptos, reparto=("50.00", "50.00")):
        sufijo = uuid.uuid4().hex[:8]
        cps = []
        with get_engine().begin() as conn:
            prop = conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                                {"d": f"Calle de prueba {sufijo}"}).scalar_one()
            creadas.append(prop)
            for i, (estado, sep, ago) in enumerate(conceptos):
                concepto = conn.execute(
                    text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                    {"n": f"C{i} {sufijo}"}).scalar_one()
                cp = conn.execute(
                    text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                            VALUES (:p, :c) RETURNING id"""),
                    {"p": prop, "c": concepto}).scalar_one()
                cps.append(cp)
                conn.execute(
                    text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado)
                            VALUES (:p, :per, :cp, :e)"""),
                    {"p": prop, "per": SEP, "cp": cp, "e": estado})
                for periodo, importe in ((SEP, sep), (AGO, ago)):
                    if importe is not None:
                        conn.execute(
                            text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                                    VALUES (:cp, :per, :imp, :u)"""),
                            {"cp": cp, "per": periodo, "imp": importe, "u": uid})
            for propietario, porcentaje in zip(PROPIETARIOS, reparto):
                if propietario not in propietarios_creados:
                    conn.execute(text("""INSERT INTO propietario (id, nombre) VALUES (:id, :n)
                                         ON CONFLICT (id) DO NOTHING"""),
                                 {"id": propietario, "n": f"Propietario {str(propietario)[-1]}"})
                    propietarios_creados.add(propietario)
                conn.execute(
                    text("""INSERT INTO propiedad_propietario (propiedad_id, propietario_id, porcentaje)
                            VALUES (:p, :o, :pct)"""),
                    {"p": prop, "o": propietario, "pct": porcentaje})
        return {"uid": uid, "headers": auth(make_token(uid)), "propiedad_id": str(prop),
                "cps": [str(c) for c in cps]}

    yield _armar

    with get_engine().begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        for prop in creadas:
            ids = conn.execute(text("SELECT id FROM preliquidacion WHERE propiedad_id = :p"),
                               {"p": prop}).scalars().all()
            for tabla in ("reparto", "preliquidacion_advertencia", "preliquidacion_detalle"):
                conn.execute(text(f"DELETE FROM {tabla} WHERE preliquidacion_id = ANY(:ids)"),
                             {"ids": ids})
            conn.execute(text("DELETE FROM preliquidacion WHERE propiedad_id = :p"), {"p": prop})
            cps = conn.execute(text("SELECT id FROM concepto_propiedad WHERE propiedad_id = :p"),
                               {"p": prop}).scalars().all()
            conceptos = conn.execute(
                text("SELECT concepto_id FROM concepto_propiedad WHERE propiedad_id = :p"),
                {"p": prop}).scalars().all()
            conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                         {"ids": cps})
            conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop})
            conn.execute(text("DELETE FROM propiedad_propietario WHERE propiedad_id = :p"), {"p": prop})
            conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop})
            conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": conceptos})
            conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop})
        conn.execute(text("DELETE FROM propietario WHERE id = ANY(:ids)"),
                     {"ids": list(propietarios_creados)})


def _generar(client, esc, confirmar=False):
    return client.post("/preliquidaciones", headers=esc["headers"], json={
        "propiedad_id": esc["propiedad_id"], "periodo": PERIODO,
        "confirmar_pendientes": confirmar})


def _cantidad_preliquidaciones(propiedad_id):
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT count(*) FROM preliquidacion WHERE propiedad_id = :p"),
                            {"p": propiedad_id}).scalar_one()


def _tipos(body):
    return sorted(a["tipo"] for a in body["advertencias"])


# --- Criterios 1 y 2: pendientes ---------------------------------------------

def test_con_pendiente_sin_confirmar_no_genera_e_informa_el_pendiente(client, armar):
    esc = armar([("cargado", "1000.00", None), ("pendiente", None, None)])

    r = _generar(client, esc)

    assert r.status_code == 409, r.text
    body = r.json()
    assert body["codigo"] == "pendientes_sin_confirmar"
    assert [p["concepto_propiedad_id"] for p in body["detalle"]["pendientes"]] == [esc["cps"][1]]
    assert _cantidad_preliquidaciones(esc["propiedad_id"]) == 0


def test_confirmando_genera_la_version_1_con_un_pendiente_confirmado_por_pendiente(client, armar):
    esc = armar([("cargado", "1000.00", None), ("pendiente", None, None), ("pendiente", None, None)])

    r = _generar(client, esc, confirmar=True)

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["version"] == 1
    assert _tipos(body).count("pendiente_confirmado") == 2
    assert len(body["detalle"]) == 1  # los pendientes no entran al detalle


# --- Criterio 3: detalle solo con cargados ------------------------------------

def test_detalle_solo_con_cargados_y_total_es_la_suma(client, armar):
    esc = armar([("cargado", "8000.00", None), ("cargado", "0.00", None),
                 ("cargado", "2000.00", None), ("no_corresponde", None, None)])

    r = _generar(client, esc)

    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body["detalle"]) == 3
    assert sorted(d["importe"] for d in body["detalle"]) == ["0.00", "2000.00", "8000.00"]
    assert body["importe_total"] == "10000.00"


# --- Criterio 4: reparto con redondeo -----------------------------------------

def test_reparto_de_10_pesos_en_tercios(client, armar):
    esc = armar([("cargado", "10.00", None)], reparto=("33.33", "33.33", "33.34"))

    r = _generar(client, esc)

    assert r.status_code == 201, r.text
    reparto = r.json()["reparto"]
    assert [x["propietario_id"] for x in reparto] == [str(p) for p in PROPIETARIOS]
    assert [x["importe_correspondiente"] for x in reparto] == ["3.33", "3.33", "3.34"]
    assert [x["porcentaje_aplicado"] for x in reparto] == ["33.33", "33.33", "33.34"]
    assert sum(Decimal(x["importe_correspondiente"]) for x in reparto) == Decimal("10.00")


# --- Criterio 5: total negativo -----------------------------------------------

def test_total_negativo_advierte_y_reparte_negativo(client, armar):
    esc = armar([("cargado", "-500.00", None)])

    r = _generar(client, esc)

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["importe_total"] == "-500.00"
    assert "total_negativo" in _tipos(body)
    assert [x["importe_correspondiente"] for x in body["reparto"]] == ["-250.00", "-250.00"]


# --- HU-10 criterio 5: las advertencias no bloquean y se guardan --------------

def test_las_advertencias_de_variacion_no_impiden_generar_y_quedan_guardadas(client, armar):
    esc = armar([("cargado", "1350.00", "1000.00"),   # 35 %: variacion_inusual
                 ("cargado", "500.00", None)])        # sin agosto: sin_referencia

    r = _generar(client, esc)

    assert r.status_code == 201, r.text
    assert _tipos(r.json()) == ["sin_referencia", "variacion_inusual"]
    with get_engine().connect() as conn:
        guardadas = conn.execute(text("""
            SELECT a.tipo FROM preliquidacion_advertencia a
            JOIN preliquidacion p ON p.id = a.preliquidacion_id
            WHERE p.propiedad_id = :p ORDER BY a.tipo"""),
            {"p": esc["propiedad_id"]}).scalars().all()
    assert guardadas == ["sin_referencia", "variacion_inusual"]


# --- Versión, auditoría y conflictos ------------------------------------------

def test_generar_otra_vez_crea_la_version_2(client, armar):
    esc = armar([("cargado", "1000.00", None)])

    v1 = _generar(client, esc)
    v2 = _generar(client, esc)

    assert (v1.json()["version"], v2.json()["version"]) == (1, 2)
    assert _cantidad_preliquidaciones(esc["propiedad_id"]) == 2


def test_la_generacion_queda_auditada(client, armar):
    esc = armar([("cargado", "1000.00", None)])

    r = _generar(client, esc)

    with get_engine().connect() as conn:
        registro = conn.execute(text("""
            SELECT usuario_id, accion, detalle FROM auditoria
            WHERE entidad = 'preliquidacion' AND entidad_id = :id"""),
            {"id": r.json()["id"]}).mappings().one()
    assert registro["usuario_id"] == esc["uid"]
    assert registro["accion"] == "generar_preliquidacion"
    assert registro["detalle"]["version"] == 1
    assert registro["detalle"]["importe_total"] == "1000.00"


def test_choque_de_version_responde_409_sin_dejar_nada_a_medias(client, armar, monkeypatch):
    """Simula dos generaciones simultáneas: la segunda calcula la misma versión que la
    primera ya guardó. La base la rechaza (UNIQUE) y no queda ninguna fila suelta."""
    from app.modules.preliquidaciones import repository

    esc = armar([("cargado", "1000.00", None)])
    assert _generar(client, esc).status_code == 201
    monkeypatch.setattr(repository, "siguiente_version", lambda *a, **k: 1)

    r = _generar(client, esc)

    assert r.status_code == 409, r.text
    assert r.json()["codigo"] == "version_en_conflicto"
    assert _cantidad_preliquidaciones(esc["propiedad_id"]) == 1
    with get_engine().connect() as conn:
        huerfanos = conn.execute(text("""
            SELECT count(*) FROM preliquidacion_detalle d
            LEFT JOIN preliquidacion p ON p.id = d.preliquidacion_id WHERE p.id IS NULL""")).scalar_one()
    assert huerfanos == 0


@pytest.mark.parametrize(("reparto", "codigo"), [
    ((), "propiedad_sin_reparto"),
    (("50.00", "40.00"), "reparto_invalido"),
])
def test_reparto_faltante_o_invalido_responde_409(client, armar, reparto, codigo):
    esc = armar([("cargado", "1000.00", None)], reparto=reparto)

    r = _generar(client, esc)

    assert r.status_code == 409, r.text
    assert r.json()["codigo"] == codigo
    assert _cantidad_preliquidaciones(esc["propiedad_id"]) == 0


def test_periodo_sin_checklist_responde_409(client, armar):
    esc = armar([])  # propiedad sin checklist en septiembre

    r = _generar(client, esc)

    assert r.status_code == 409, r.text
    assert r.json()["codigo"] == "periodo_sin_checklist"


def test_propiedad_inexistente_responde_404(client, armar):
    esc = armar([("cargado", "1000.00", None)])
    esc["propiedad_id"] = str(uuid.uuid4())

    r = _generar(client, esc)

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "propiedad_no_encontrada"


# --- HU-09 criterio 4 (cierra B3) ----------------------------------------------

def test_no_corresponde_despues_de_v1_no_cambia_v1_y_v2_no_lo_incluye(client, armar):
    esc = armar([("cargado", "86200.00", None), ("cargado", "1000.00", None)])
    v1 = _generar(client, esc).json()

    with get_engine().connect() as conn:
        fila = conn.execute(text("""SELECT id FROM checklist_periodo
                                    WHERE concepto_propiedad_id = :cp AND periodo = :per"""),
                            {"cp": esc["cps"][0], "per": SEP}).scalar_one()
    assert client.post(f"/checklist/{fila}/no-corresponde",
                       headers=esc["headers"]).status_code == 200
    v2 = _generar(client, esc).json()

    assert len(v2["detalle"]) == 1 and v2["importe_total"] == "1000.00"
    # La versión 1 se vuelve a leer del snapshot y es idéntica a la que se generó.
    with Session(get_engine()) as sesion:
        v1_despues = obtener(sesion, uuid.UUID(v1["id"])).model_dump(mode="json")
    assert v1_despues == v1
