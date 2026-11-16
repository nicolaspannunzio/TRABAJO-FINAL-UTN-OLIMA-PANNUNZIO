import json
from uuid import UUID

from sqlalchemy import insert
from sqlmodel import Session

from app.audit.models import Auditoria


def registrar(session: Session, usuario_id: UUID, accion: str, entidad: str,
              entidad_id: UUID | None = None, detalle: dict | None = None) -> None:
    """Agrega una fila a `auditoria` dentro de la transacción de la sesión recibida.

    No hace commit: se confirma o se revierte junto con el cambio de negocio.
    """
    # Decimal, UUID y datetime se guardan como texto, nunca como float.
    detalle_json = json.loads(json.dumps(detalle or {}, default=str))
    session.connection().execute(
        insert(Auditoria.__table__).values(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle_json,
        )
    )