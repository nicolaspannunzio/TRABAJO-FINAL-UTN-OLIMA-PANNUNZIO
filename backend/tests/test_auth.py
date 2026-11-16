import pytest
import time
from app.core.deps import require_admin
from app.main import app
from fastapi import Depends

app.add_api_route("/_test/solo-admin", lambda: {"ok": True}, methods=["GET"],
                  dependencies=[Depends(require_admin)], include_in_schema=False)


def test_sin_token_401(client):
    r = client.get("/me")
    assert r.status_code == 401
    assert r.json()["codigo"] == "no_autenticado"


def test_token_invalido_401(client, auth):
    r = client.get("/me", headers=auth("esto.no.es.un.jwt"))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"


def test_token_firmado_con_otro_secreto_401(client, crear_usuario, make_token, auth):
    uid = crear_usuario()
    token = make_token(uid, secret="otro-secreto-otro-secreto-otro-secreto-123")
    assert client.get("/me", headers=auth(token)).status_code == 401


def test_token_expirado_401(client, crear_usuario, make_token, auth):
    uid = crear_usuario()
    r = client.get("/me", headers=auth(make_token(uid, expira_en=-10)))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_expirado"


def test_usuario_inactivo_403(client, crear_usuario, make_token, auth):
    uid = crear_usuario(activo=False)
    r = client.get("/me", headers=auth(make_token(uid)))
    assert r.status_code == 403
    assert r.json()["codigo"] == "usuario_inactivo"


def test_me_devuelve_usuario_y_rol(client, crear_usuario, make_token, auth):
    uid = crear_usuario(rol="operador")
    r = client.get("/me", headers=auth(make_token(uid)))
    assert r.status_code == 200
    assert r.json()["id"] == str(uid)
    assert r.json()["rol"] == "operador"


def test_operador_rechazado_por_require_admin(client, crear_usuario, make_token, auth):
    uid = crear_usuario(rol="operador")
    r = client.get("/_test/solo-admin", headers=auth(make_token(uid)))
    assert r.status_code == 403
    assert r.json()["codigo"] == "permiso_insuficiente"


def test_admin_pasa_require_admin(client, crear_usuario, make_token, auth):
    uid = crear_usuario(rol="admin")
    assert client.get("/_test/solo-admin", headers=auth(make_token(uid))).status_code == 200


def test_propiedades_requiere_token_y_lista(client, crear_usuario, make_token, auth):
    assert client.get("/propiedades").status_code == 401
    uid = crear_usuario()
    r = client.get("/propiedades", headers=auth(make_token(uid)))
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    
def _claims(**extra):
    base = {"aud": "authenticated", "exp": int(time.time()) + 3600}
    base.update(extra)
    return base


def test_token_sin_exp_401(client, crear_usuario, make_raw_token, auth):
    uid = crear_usuario()
    claims = {"sub": str(uid), "aud": "authenticated"}  # sin exp: nunca vence
    r = client.get("/me", headers=auth(make_raw_token(claims)))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"


def test_token_sin_sub_401(client, make_raw_token, auth):
    r = client.get("/me", headers=auth(make_raw_token(_claims())))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"


@pytest.mark.parametrize("sub", ["no-es-un-uuid", 123, None])
def test_token_con_sub_invalido_401(client, make_raw_token, auth, sub):
    r = client.get("/me", headers=auth(make_raw_token(_claims(sub=sub))))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"


def test_token_con_audiencia_incorrecta_401(client, crear_usuario, make_raw_token, auth):
    uid = crear_usuario()
    r = client.get("/me", headers=auth(make_raw_token(_claims(sub=str(uid), aud="anon"))))
    assert r.status_code == 401
    assert r.json()["codigo"] == "token_invalido"