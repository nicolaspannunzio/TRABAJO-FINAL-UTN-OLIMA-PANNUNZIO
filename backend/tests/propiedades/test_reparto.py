"""A4 / HU-03 criterio 2 y HU-04 criterios 1 a 3, más atomicidad.

Cada test crea sus datos (prefijo "A4-test") y los borra al terminar.
"""
import threading
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import get_engine
from app.modules.propiedades import repository, service
from app.modules.propiedades.schemas import RepartoEntrada

PREFIJO = "A4-test"


@pytest.fixture
def headers(crear_usuario, make_token, auth):
    return auth(make_token(crear_usuario("operador")))


@pytest.fixture(autouse=True)
def limpiar():
    yield
    with get_engine().begin() as conn:
        conn.execute(text(
            "DELETE FROM propiedad_propietario WHERE propiedad_id IN "
            "(SELECT id FROM propiedad WHERE direccion LIKE :p)"), {"p": f"{PREFIJO}%"})
        conn.execute(text("DELETE FROM propiedad WHERE direccion LIKE :p"), {"p": f"{PREFIJO}%"})
        conn.execute(text("DELETE FROM propietario WHERE nombre LIKE :p"), {"p": f"{PREFIJO}%"})


def _propiedad() -> uuid.UUID:
    with get_engine().begin() as conn:
        return conn.execute(text("INSERT INTO propiedad (direccion) VALUES (:d) RETURNING id"),
                            {"d": f"{PREFIJO} Calle {uuid.uuid4().hex[:8]}"}).scalar_one()


def _propietario(nombre: str) -> uuid.UUID:
    with get_engine().begin() as conn:
        return conn.execute(text("INSERT INTO propietario (nombre) VALUES (:n) RETURNING id"),
                            {"n": f"{PREFIJO} {nombre}"}).scalar_one()


def _leer(propiedad_id) -> dict:
    with get_engine().connect() as conn:
        filas = conn.execute(text(
            "SELECT propietario_id, porcentaje FROM propiedad_propietario WHERE propiedad_id = :p"),
            {"p": propiedad_id}).all()
    return {fila[0]: fila[1] for fila in filas}


def _put(client, headers, propiedad_id, reparto):
    cuerpo = [{"propietario_id": str(p), "porcentaje": pct} for p, pct in reparto]
    return client.put(f"/propiedades/{propiedad_id}/propietarios", json=cuerpo, headers=headers)


@pytest.fixture
def con_50_50(client, headers):
    pid, a, b = _propiedad(), _propietario("Ana"), _propietario("Beto")
    assert _put(client, headers, pid, [(a, "50.00"), (b, "50.00")]).status_code == 200
    return pid, a, b


# --- HU-04 criterio 1 ------------------------------------------------------------

def test_cambiar_de_50_50_a_60_40(client, headers, con_50_50):
    pid, a, b = con_50_50
    r = _put(client, headers, pid, [(a, "60.00"), (b, "40.00")])
    assert r.status_code == 200
    assert [(x["nombre"][-3:], x["porcentaje"]) for x in r.json()] == [("Ana", "60.00"), ("eto", "40.00")]
    assert _leer(pid) == {a: Decimal("60.00"), b: Decimal("40.00")}
    assert client.get(f"/propiedades/{pid}/propietarios", headers=headers).json() == r.json()


# --- HU-04 criterio 2 ------------------------------------------------------------

@pytest.mark.parametrize("pct_a,pct_b", [("50.00", "40.00"), ("60.00", "50.00")])
def test_suma_90_o_110_se_rechaza_y_conserva_lo_anterior(client, headers, con_50_50, pct_a, pct_b):
    pid, a, b = con_50_50
    r = _put(client, headers, pid, [(a, pct_a), (b, pct_b)])
    assert r.status_code == 422 and r.json()["codigo"] == "reparto_suma_invalida"
    assert _leer(pid) == {a: Decimal("50.00"), b: Decimal("50.00")}


# --- HU-04 criterio 3 ------------------------------------------------------------

@pytest.mark.parametrize("malo", ["0", "0.00", "100.01", "-5.00", "150.00"])
def test_porcentaje_fuera_de_rango_se_rechaza(client, headers, con_50_50, malo):
    pid, a, b = con_50_50
    r = _put(client, headers, pid, [(a, malo), (b, "40.00")])
    assert r.status_code == 422
    assert _leer(pid) == {a: Decimal("50.00"), b: Decimal("50.00")}


# --- HU-03 criterio 2 ------------------------------------------------------------

def test_propietario_repetido_se_rechaza(client, headers, con_50_50):
    pid, a, _ = con_50_50
    r = _put(client, headers, pid, [(a, "50.00"), (a, "50.00")])
    assert r.status_code == 422 and r.json()["codigo"] == "propietario_repetido"
    assert len(_leer(pid)) == 2


def test_reenviar_el_mismo_propietario_reemplaza_no_duplica(client, headers, con_50_50):
    pid, a, _ = con_50_50
    assert _put(client, headers, pid, [(a, "100.00")]).status_code == 200
    assert _leer(pid) == {a: Decimal("100.00")}


# --- Errores 404 -----------------------------------------------------------------

def test_propietario_inexistente_da_404_y_conserva(client, headers, con_50_50):
    pid, a, _ = con_50_50
    r = _put(client, headers, pid, [(a, "50.00"), (uuid.uuid4(), "50.00")])
    assert r.status_code == 404 and r.json()["codigo"] == "propietario_no_encontrado"
    assert len(_leer(pid)) == 2


def test_propiedad_inexistente_da_404(client, headers):
    r = _put(client, headers, uuid.uuid4(), [(_propietario("Ana"), "100.00")])
    assert r.status_code == 404 and r.json()["codigo"] == "propiedad_no_encontrada"
    r = client.get(f"/propiedades/{uuid.uuid4()}/propietarios", headers=headers)
    assert r.status_code == 404


def test_propiedad_sin_reparto_devuelve_lista_vacia(client, headers):
    r = client.get(f"/propiedades/{_propiedad()}/propietarios", headers=headers)
    assert r.status_code == 200 and r.json() == []


# --- Atomicidad ------------------------------------------------------------------

def test_un_fallo_a_mitad_conserva_los_porcentajes_anteriores(con_50_50, monkeypatch):
    pid, a, b = con_50_50
    original = repository._agregar_fila
    llamadas = []

    def falla_en_la_segunda(*args, **kwargs):
        llamadas.append(1)
        if len(llamadas) == 2:
            raise RuntimeError("falla simulada")
        return original(*args, **kwargs)

    monkeypatch.setattr(repository, "_agregar_fila", falla_en_la_segunda)
    nuevo = [RepartoEntrada(propietario_id=a, porcentaje=Decimal("60.00")),
             RepartoEntrada(propietario_id=b, porcentaje=Decimal("40.00"))]
    with Session(get_engine()) as session:
        with pytest.raises(RuntimeError):
            service.reemplazar_reparto(session, pid, nuevo)
    assert _leer(pid) == {a: Decimal("50.00"), b: Decimal("50.00")}


def test_nunca_se_lee_un_estado_intermedio(client, headers, con_50_50):
    pid, a, b = con_50_50
    sumas, terminar = [], threading.Event()

    def lector():
        while not terminar.is_set():
            with get_engine().connect() as conn:
                filas = conn.execute(text(
                    "SELECT porcentaje FROM propiedad_propietario WHERE propiedad_id = :p"),
                    {"p": pid}).scalars().all()
            sumas.append((len(filas), sum(filas)))

    hilo = threading.Thread(target=lector)
    hilo.start()
    try:
        for i in range(20):
            reparto = [(a, "60.00"), (b, "40.00")] if i % 2 == 0 else [(a, "50.00"), (b, "50.00")]
            assert _put(client, headers, pid, reparto).status_code == 200
    finally:
        terminar.set()
        hilo.join()
    assert sumas and all(s == (2, Decimal("100")) for s in sumas)