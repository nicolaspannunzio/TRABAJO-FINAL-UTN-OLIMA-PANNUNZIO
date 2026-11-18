"""B4 / HU-10: GET /advertencias contra la base (prueba integrada de la vista previa).

Agosto 2026 tiene importes de referencia; septiembre está abierto con importes cargados.
Cada concepto reproduce un criterio de HU-10:

    Concepto            Umbral  Ago      Sep      Esperado
    A: global 35 %      —       1000     1350     variacion_inusual   (criterio 1)
    B: global 20 %      —       1000     1200     nada                (criterio 1)
    C: propio 50 %      50      1000     1350     nada                (criterio 2)
    D: a negativo       —       1000     -200     variacion_inusual   (criterio 3)
    E: sin agosto       —       —        1350     sin_referencia      (criterio 4)
    F: agosto en 0      —       0        1350     sin_referencia      (criterio 4)
    G: pendiente        —       1000     —        nada (no se evalúa)
    H: no corresponde   —       1000     —        nada (no se evalúa)

El criterio 5 (las advertencias no impiden generar) se cierra con B6: la vista previa no
persiste nada ni bloquea ninguna operación.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import get_engine

AGO, SEP = date(2026, 8, 1), date(2026, 9, 1)

#          clave, umbral, agosto, septiembre, estado en septiembre
CASOS = [
    ("A", None, "1000.00", "1350.00", "cargado"),
    ("B", None, "1000.00", "1200.00", "cargado"),
    ("C", "50.00", "1000.00", "1350.00", "cargado"),
    ("D", None, "1000.00", "-200.00", "cargado"),
    ("E", None, None, "1350.00", "cargado"),
    ("F", None, "0.00", "1350.00", "cargado"),
    ("G", None, "1000.00", None, "pendiente"),
    ("H", None, "1000.00", None, "no_corresponde"),
]


@pytest.fixture
def escenario(crear_usuario, make_token, auth, monkeypatch):
    # El umbral global puede venir de backend/.env: el test fija el valor de las fuentes (30 %).
    monkeypatch.setattr(get_settings(), "umbral_variacion_default_pct", Decimal("30.00"))
    uid = crear_usuario("operador")
    sufijo = uuid.uuid4().hex[:8]
    cps, concepto_ids = {}, []

    with get_engine().begin() as conn:
        prop_id = conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                               {"d": f"Calle de prueba {sufijo}"}).scalar_one()
        for clave, umbral, ago, sep, estado in CASOS:
            concepto_id = conn.execute(
                text("""INSERT INTO concepto (nombre, umbral_variacion_pct)
                        VALUES (:n, :u) RETURNING id"""),
                {"n": f"{clave} {sufijo}", "u": umbral},
            ).scalar_one()
            concepto_ids.append(concepto_id)
            cp = conn.execute(
                text("""INSERT INTO concepto_propiedad (propiedad_id, concepto_id)
                        VALUES (:p, :c) RETURNING id"""),
                {"p": prop_id, "c": concepto_id},
            ).scalar_one()
            cps[clave] = cp
            conn.execute(
                text("""INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado)
                        VALUES (:p, :per, :cp, :e)"""),
                {"p": prop_id, "per": SEP, "cp": cp, "e": estado},
            )
            for periodo, importe in ((AGO, ago), (SEP, sep)):
                if importe is not None:
                    conn.execute(
                        text("""INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
                                VALUES (:cp, :per, :imp, :u)"""),
                        {"cp": cp, "per": periodo, "imp": importe, "u": uid},
                    )

    yield {"headers": auth(make_token(uid)), "propiedad_id": str(prop_id),
           "cps": {k: str(v) for k, v in cps.items()}}

    with get_engine().begin() as conn:
        ids = list(cps.values())
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                     {"ids": ids})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = :p"), {"p": prop_id})
        conn.execute(text("DELETE FROM concepto WHERE id = ANY(:ids)"), {"ids": concepto_ids})
        conn.execute(text("DELETE FROM propiedad WHERE id = :p"), {"p": prop_id})


def _vista_previa(client, esc, periodo="2026-09-01"):
    return client.get("/advertencias", headers=esc["headers"],
                      params={"propiedad_id": esc["propiedad_id"], "periodo": periodo})


def test_vista_previa_aplica_los_criterios_de_hu10(client, escenario):
    r = _vista_previa(client, escenario)

    assert r.status_code == 200, r.text
    por_concepto = {a["concepto_propiedad_id"]: a for a in r.json()}
    cps = escenario["cps"]
    esperado = {
        cps["A"]: "variacion_inusual",
        cps["D"]: "variacion_inusual",
        cps["E"]: "sin_referencia",
        cps["F"]: "sin_referencia",
    }
    assert {k: v["tipo"] for k, v in por_concepto.items()} == esperado
    # B (20 %), C (umbral propio 50 %), G (pendiente) y H (no corresponde) no tienen advertencia.

    assert "35.00 %" in por_concepto[cps["A"]]["detalle"]
    assert "120.00 %" in por_concepto[cps["D"]]["detalle"]
    assert "sin importe" in por_concepto[cps["E"]]["detalle"]
    assert "importe en 0" in por_concepto[cps["F"]]["detalle"]


def test_vista_previa_no_persiste_nada(client, escenario):
    with get_engine().connect() as conn:
        antes = conn.execute(text("SELECT count(*) FROM preliquidacion_advertencia")).scalar_one()

    _vista_previa(client, escenario)

    with get_engine().connect() as conn:
        despues = conn.execute(text("SELECT count(*) FROM preliquidacion_advertencia")).scalar_one()
    assert despues == antes


def test_periodo_sin_abrir_devuelve_404(client, escenario):
    r = _vista_previa(client, escenario, periodo="2026-10-01")

    assert r.status_code == 404, r.text
    assert r.json()["codigo"] == "checklist_no_encontrado"


@pytest.mark.parametrize(("periodo", "anterior"), [
    (date(2026, 9, 1), date(2026, 8, 1)),
    (date(2026, 1, 1), date(2025, 12, 1)),
])
def test_periodo_anterior(periodo, anterior):
    from app.modules.advertencias.service import periodo_anterior

    assert periodo_anterior(periodo) == anterior
