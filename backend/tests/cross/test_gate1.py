"""Gate 1: pruebas que cruzan el corte de A (configuración) y el de B (período y preliquidación).

- HU-04, criterio 4: cambiar los porcentajes de reparto no altera una preliquidación ya generada.
- HU-06, criterio 2: un concepto desactivado en la plantilla no aparece en el checklist que se
  abre después.

Todo se hace por la API, como lo haría el frontend. Cada test crea sus propios datos
(prefijo "Cross-test") y los borra al terminar.

Las tablas de la preliquidación son inmutables (triggers). Para limpiar, el cierre usa
session_replication_role = replica, que apaga los triggers SOLO en esa conexión de la base
de pruebas. Nunca se hace algo así fuera de los tests.
"""
import uuid

import pytest
from app.core.db import get_engine
from sqlalchemy import text

PREFIJO = "Cross-test"
PERIODO = "2026-10-01"


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def headers(crear_usuario, make_token, auth):
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture(autouse=True)
def limpiar(headers):
    # Depende de `headers` para que se cierre ANTES de borrar el usuario de prueba
    # (los importes y preliquidaciones apuntan a ese usuario).
    yield
    with get_engine().begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        like = {"p": f"{PREFIJO}%"}
        props = conn.execute(text("SELECT id FROM propiedad WHERE direccion LIKE :p"),
                             like).scalars().all()
        preliqs = conn.execute(text("SELECT id FROM preliquidacion WHERE propiedad_id = ANY(:ids)"),
                               {"ids": props}).scalars().all()
        cps = conn.execute(text("SELECT id FROM concepto_propiedad WHERE propiedad_id = ANY(:ids)"),
                           {"ids": props}).scalars().all()
        for tabla in ("reparto", "preliquidacion_advertencia", "preliquidacion_detalle"):
            conn.execute(text(f"DELETE FROM {tabla} WHERE preliquidacion_id = ANY(:ids)"),
                         {"ids": preliqs})
        conn.execute(text("DELETE FROM preliquidacion WHERE id = ANY(:ids)"), {"ids": preliqs})
        conn.execute(text("DELETE FROM importe_mensual WHERE concepto_propiedad_id = ANY(:ids)"),
                     {"ids": cps})
        conn.execute(text("DELETE FROM checklist_periodo WHERE propiedad_id = ANY(:ids)"),
                     {"ids": props})
        conn.execute(text("DELETE FROM propiedad_propietario WHERE propiedad_id = ANY(:ids)"),
                     {"ids": props})
        conn.execute(text("DELETE FROM concepto_propiedad WHERE propiedad_id = ANY(:ids)"),
                     {"ids": props})
        conn.execute(text("DELETE FROM propiedad WHERE id = ANY(:ids)"), {"ids": props})
        conn.execute(text("DELETE FROM concepto WHERE nombre LIKE :p"), like)
        conn.execute(text("DELETE FROM propietario WHERE nombre LIKE :p"), like)


# --- Datos de apoyo ------------------------------------------------------------

def _propiedad() -> str:
    with get_engine().begin() as conn:
        return str(conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                                {"d": f"{PREFIJO} {uuid.uuid4().hex[:8]}"}).scalar_one())


def _propietario(nombre: str) -> str:
    with get_engine().begin() as conn:
        return str(conn.execute(text("INSERT INTO propietario (nombre) VALUES (:n) RETURNING id"),
                                {"n": f"{PREFIJO} {nombre} {uuid.uuid4().hex[:6]}"}).scalar_one())


def _concepto() -> str:
    with get_engine().begin() as conn:
        return str(conn.execute(text("INSERT INTO concepto (nombre) VALUES (:n) RETURNING id"),
                                {"n": f"{PREFIJO} {uuid.uuid4().hex[:8]}"}).scalar_one())


def _asociar(client, headers, propiedad_id: str, concepto_id: str) -> dict:
    r = client.post(f"/propiedades/{propiedad_id}/conceptos", json={"concepto_id": concepto_id},
                    headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _repartir(client, headers, propiedad_id: str, reparto: list[tuple[str, str]]):
    cuerpo = [{"propietario_id": p, "porcentaje": pct} for p, pct in reparto]
    return client.put(f"/propiedades/{propiedad_id}/propietarios", json=cuerpo, headers=headers)


# --- HU-04, criterio 4 ----------------------------------------------------------

def test_cambiar_porcentajes_no_altera_una_preliquidacion_generada(client, headers):
    p, ana, beto = _propiedad(), _propietario("Ana"), _propietario("Beto")
    cp = _asociar(client, headers, p, _concepto())["id"]
    assert _repartir(client, headers, p, [(ana, "50.00"), (beto, "50.00")]).status_code == 200

    # Se abre el período, se carga un importe y se genera la versión 1 (50/50).
    assert client.post("/checklist", json={"propiedad_id": p, "periodo": PERIODO},
                       headers=headers).status_code == 201
    assert client.post("/importes", headers=headers, json={
        "propiedad_id": p, "periodo": PERIODO, "concepto_propiedad_id": cp,
        "importe": "1000.00"}).status_code == 201
    r = client.post("/preliquidaciones", headers=headers, json={
        "propiedad_id": p, "periodo": PERIODO, "confirmar_pendientes": False})
    assert r.status_code == 201, r.text
    v1 = r.json()
    assert v1["version"] == 1
    assert [x["importe_correspondiente"] for x in v1["reparto"]] == ["500.00", "500.00"]
    assert [x["porcentaje_aplicado"] for x in v1["reparto"]] == ["50.00", "50.00"]

    # Se cambia el reparto a 60/40 (el reparto vigente de la propiedad sí cambia).
    assert _repartir(client, headers, p, [(ana, "60.00"), (beto, "40.00")]).status_code == 200
    actual = client.get(f"/propiedades/{p}/propietarios", headers=headers).json()
    assert sorted(x["porcentaje"] for x in actual) == ["40.00", "60.00"]

    # La versión 1 sigue idéntica: mismos porcentajes aplicados e importes.
    despues = client.get(f"/preliquidaciones/{v1['id']}", headers=headers)
    assert despues.status_code == 200
    assert despues.json() == v1

    # Y no se creó ninguna versión nueva por haber cambiado el reparto.
    params = {"propiedad_id": p, "periodo": PERIODO}
    versiones = client.get("/preliquidaciones", params=params, headers=headers).json()
    assert [v["id"] for v in versiones] == [v1["id"]]
    vigente = client.get("/preliquidaciones/vigente", params=params, headers=headers).json()
    assert vigente["id"] == v1["id"]


# --- HU-06, criterio 2 ----------------------------------------------------------

def test_concepto_desactivado_no_aparece_en_el_checklist_que_se_abre_despues(client, headers):
    p = _propiedad()
    activo = _asociar(client, headers, p, _concepto())
    desactivado = _asociar(client, headers, p, _concepto())
    r = client.patch(f"/propiedades/{p}/conceptos/{desactivado['id']}",
                     json={"activo": False}, headers=headers)
    assert r.status_code == 200 and r.json()["activo"] is False

    r = client.post("/checklist", json={"propiedad_id": p, "periodo": PERIODO}, headers=headers)
    assert r.status_code == 201, r.text
    filas = r.json()["filas"]
    assert [f["concepto_propiedad_id"] for f in filas] == [activo["id"]]
    assert all(f["estado"] == "pendiente" for f in filas)

    # En la base tampoco hay fila para el concepto inactivo.
    with get_engine().connect() as conn:
        n = conn.execute(text("""SELECT count(*) FROM checklist_periodo
                                 WHERE propiedad_id = :p AND concepto_propiedad_id = :cp"""),
                         {"p": p, "cp": desactivado["id"]}).scalar_one()
    assert n == 0

    # Al consultar el checklist se ve lo mismo, y el concepto sigue en la plantilla (inactivo).
    get = client.get("/checklist", params={"propiedad_id": p, "periodo": PERIODO}, headers=headers)
    assert [f["concepto_propiedad_id"] for f in get.json()["filas"]] == [activo["id"]]
    plantilla = client.get(f"/propiedades/{p}/conceptos", headers=headers).json()
    assert sorted(f["activo"] for f in plantilla) == [False, True]