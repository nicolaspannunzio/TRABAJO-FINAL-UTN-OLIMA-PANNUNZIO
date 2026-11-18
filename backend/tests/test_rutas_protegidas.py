"""A1 / HU-01 criterios 2 y 3: ninguna ruta de datos responde sin token válido
ni a un usuario inactivo. Recorre openapi: una ruta nueva queda cubierta sola."""
import re
import uuid

import pytest

from app.main import app

_METODOS = {"get", "post", "put", "patch", "delete"}


def _rutas():
    return [(m.upper(), p) for p, ops in app.openapi()["paths"].items()
            if p != "/health" for m in ops if m in _METODOS]


RUTAS = _rutas()
IDS = [f"{m} {p}" for m, p in RUTAS]


def _url(path: str) -> str:
    return re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)


def test_el_recorrido_no_pasa_en_vacio():
    assert ("GET", "/me") in RUTAS
    assert len(RUTAS) > 10


@pytest.mark.parametrize("metodo, path", RUTAS, ids=IDS)
def test_sin_token_401(client, metodo, path):
    r = client.request(metodo, _url(path))
    assert r.status_code == 401, f"{metodo} {path} respondió {r.status_code} sin token"
    assert r.json()["codigo"] == "no_autenticado"


@pytest.mark.parametrize("metodo, path", RUTAS, ids=IDS)
def test_token_invalido_401(client, auth, metodo, path):
    r = client.request(metodo, _url(path), headers=auth("esto.no.es.un.jwt"))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"


@pytest.mark.parametrize("metodo, path", RUTAS, ids=IDS)
def test_usuario_inactivo_403(client, crear_usuario, make_token, auth, metodo, path):
    token = make_token(crear_usuario(activo=False))
    r = client.request(metodo, _url(path), headers=auth(token))
    assert r.status_code == 403, f"{metodo} {path} respondió {r.status_code} a un inactivo"
    assert r.json()["codigo"] == "usuario_inactivo"