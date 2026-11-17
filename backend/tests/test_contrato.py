"""F0-08: formato de error del contrato y openapi.json al día."""
import json
import uuid

import pytest

from scripts.generar_openapi import RUTA, contenido


@pytest.mark.parametrize("metodo, url, cuerpo, campo", [
    ("post", "/checklist", {"propiedad_id": "{p}", "periodo": "2026-09-15"}, "body.periodo"),
    ("get", "/checklist?propiedad_id={p}&periodo=2026-09-15", None, "query.periodo"),
    ("post", "/importes", {"propiedad_id": "{p}", "periodo": "2026-09-01",
                           "concepto_propiedad_id": "{p}", "importe": 15000.5}, "body.importe"),
])
def test_422_de_validacion_usa_formato_del_contrato(client, crear_usuario, make_token, auth,
                                                     metodo, url, cuerpo, campo):
    p = str(uuid.uuid4())
    if cuerpo:
        cuerpo = {k: (p if v == "{p}" else v) for k, v in cuerpo.items()}
    r = getattr(client, metodo)(url.format(p=p), headers=auth(make_token(crear_usuario())),
                                **({"json": cuerpo} if cuerpo else {}))

    assert r.status_code == 422
    body = r.json()
    assert set(body) == {"codigo", "mensaje", "detalle"}
    assert body["codigo"] == "validacion"
    assert campo in [e["campo"] for e in body["detalle"]["errores"]]


def test_openapi_json_esta_actualizado():
    assert RUTA.exists(), "Falta docs/openapi.json: correr python -m scripts.generar_openapi"
    guardado = json.loads(RUTA.read_text(encoding="utf-8"))
    # Se comparan los datos, no el texto: así no influyen los finales de línea de Windows.
    assert guardado == json.loads(contenido()), (
        "docs/openapi.json no coincide con la app: correr python -m scripts.generar_openapi")