import uuid
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import select

from app.audit import registrar
from app.audit.models import Auditoria


def test_registrar_inserta_fila(db, crear_usuario):
    uid = crear_usuario()
    entidad_id = uuid.uuid4()

    registrar(db, uid, "carga_importe", "importe_mensual", entidad_id,
              {"importe": Decimal("15000.00")})
    db.commit()  # registrar no confirma por sí mismo

    fila = db.exec(select(Auditoria).where(Auditoria.usuario_id == uid)).first()
    assert fila is not None
    assert fila.accion == "carga_importe"
    assert fila.entidad == "importe_mensual"
    assert fila.entidad_id == entidad_id
    assert fila.detalle == {"importe": "15000.00"}


def test_registrar_se_revierte_con_la_transaccion(db, crear_usuario):
    uid = crear_usuario()
    registrar(db, uid, "x", "y")
    db.rollback()  # la auditoría vive en la misma transacción que el cambio de negocio

    n = db.exec(
        select(func.count()).select_from(Auditoria).where(Auditoria.usuario_id == uid)
    ).one()
    assert n == 0