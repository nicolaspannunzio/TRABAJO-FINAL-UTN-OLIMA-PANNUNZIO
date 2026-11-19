# modules/importes/repository.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, insert, select, update
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


def buscar_para_borrar(session: Session, concepto_propiedad_id: UUID, periodo: date):
    """{id, importe, cargado_por, fecha_carga} del importe del período, o None.

    FOR UPDATE: nadie lo modifica entre que se lee (para auditarlo) y se borra.
    """
    stmt = (select(_importe.c.id, _importe.c.importe, _importe.c.cargado_por,
                   _importe.c.fecha_carga)
            .where(_importe.c.concepto_propiedad_id == concepto_propiedad_id,
                   _importe.c.periodo == periodo)
            .with_for_update())
    return session.connection().execute(stmt).mappings().first()


def borrar(session: Session, importe_id: UUID) -> None:
    """No confirma: el commit lo hace el service que arma la transacción."""
    session.connection().execute(delete(_importe).where(_importe.c.id == importe_id))


def buscar_para_corregir(session: Session, importe_id: UUID):
    """La fila completa del importe, o None. FOR UPDATE: nadie la cambia hasta el commit."""
    stmt = select(_importe).where(_importe.c.id == importe_id).with_for_update()
    return session.connection().execute(stmt).mappings().first()


def actualizar_importe(session: Session, importe_id: UUID, importe: Decimal):
    """Cambia solo el importe (cargado_por y fecha_carga quedan). Devuelve la fila nueva.

    No confirma: el commit lo hace el service que arma la transacción.
    """
    stmt = (update(_importe).where(_importe.c.id == importe_id).values(importe=importe)
            .returning(*_importe.c))
    return session.connection().execute(stmt).mappings().one()
