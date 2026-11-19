from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import no_implementado, register_error_handlers
from app.main import app


def test_health_ok():
    with TestClient(app) as c:   # el `with` dispara el lifespan (abre el pool)
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base": "ok"}


def test_stub_devuelve_formato_de_error():
    """Una ruta en stub (no_implementado) responde 501 con {codigo, mensaje, detalle}.

    Usa una app mínima con los mismos manejadores de error, en lugar de una ruta real de la
    API: así el test no se rompe cada vez que una unidad implementa la ruta que se usaba
    de ejemplo (pasó con /preliquidaciones/{id} en B7).
    """
    mini = FastAPI()
    register_error_handlers(mini)

    @mini.get("/stub")
    def stub():
        raise no_implementado()

    with TestClient(mini) as c:
        r = c.get("/stub")
    assert r.status_code == 501
    assert r.json()["codigo"] == "no_implementado"
    assert set(r.json()) == {"codigo", "mensaje", "detalle"}