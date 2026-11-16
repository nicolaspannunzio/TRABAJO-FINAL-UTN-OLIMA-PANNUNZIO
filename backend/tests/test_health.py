from fastapi.testclient import TestClient
from app.main import app


def test_health_ok():
    with TestClient(app) as c:   # el `with` dispara el lifespan (abre el pool)
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base": "ok"}


def test_stub_devuelve_formato_de_error():
    with TestClient(app) as c:
        r = c.get("/conceptos")
    assert r.status_code == 501
    assert set(r.json()) == {"codigo", "mensaje", "detalle"}