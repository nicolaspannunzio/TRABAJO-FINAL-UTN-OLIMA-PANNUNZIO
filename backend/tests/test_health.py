from fastapi.testclient import TestClient
from app.main import app


def test_health_ok():
    with TestClient(app) as c:   # el `with` dispara el lifespan (abre el pool)
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base": "ok"}


def test_stub_devuelve_formato_de_error(client, crear_usuario, make_token, auth):
    uid = crear_usuario()
    r = client.get("/conceptos", headers=auth(make_token(uid)))
    assert r.status_code == 501
    assert set(r.json()) == {"codigo", "mensaje", "detalle"}