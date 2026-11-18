# modules/importes/repository.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.modules.importes.models import ImporteMensual

_importe = ImporteMensual.__table__

# Índice único de esquema_completo.sql: un importe por concepto_propiedad y período.
_UQ_IMPORTE = "uq_importe_concepto_periodo"


class ImporteDuplicado(Exception):
    """Ya existe un importe para ese concepto_propiedad y período (RN-12)."""


def insertar(session: Session, concepto_propiedad_id: UUID, periodo: date,
             importe: Decimal, cargado_por: UUID) -> UUID:
    """Inserta el importe y devuelve su id. No confirma: el commit lo hace el service.

    El duplicado se detecta por la restricción de la base, no con una consulta previa:
    así también se cubren dos cargas simultáneas (convención 7).
    """
    stmt = (insert(_importe)
            .values(concepto_propiedad_id=concepto_propiedad_id, periodo=periodo,
                    importe=importe, cargado_por=cargado_por)
            .returning(_importe.c.id))
    try:
        return session.connection().execute(stmt).scalar_one()
    except IntegrityError as e:
        diag = getattr(e.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == _UQ_IMPORTE:
            raise ImporteDuplicado from e
        raise
