# modules/checklist/repository.py
"""Acceso a datos del checklist.

Tablas de otros módulos (convención 2): se leen con table()/column() y joins explícitos,
sin importar su código.
- propiedad, concepto, concepto_propiedad: módulos de A.
- importe_mensual: módulo importes (B). Se lee con table() para que checklist no dependa
  de importes (importes sí usa este repositorio: los dos son de B).
"""
from datetime import date
from uuid import UUID

from sqlalchemy import and_, column, exists, select, table, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from app.modules.checklist.models import ChecklistPeriodo

_propiedad = table("propiedad", column("id"))
_concepto = table("concepto", column("id"), column("nombre"))
_concepto_propiedad = table("concepto_propiedad", column("id"), column("propiedad_id"),
                            column("concepto_id"), column("activo"))
_importe = table("importe_mensual", column("id"), column("concepto_propiedad_id"),
                 column("periodo"), column("importe"))

_checklist = ChecklistPeriodo.__table__


def propiedad_existe(session: Session, propiedad_id: UUID) -> bool:
    stmt = select(exists().where(_propiedad.c.id == propiedad_id))
    return bool(session.connection().execute(stmt).scalar())


def checklist_existe(session: Session, propiedad_id: UUID, periodo: date) -> bool:
    stmt = select(exists().where(_checklist.c.propiedad_id == propiedad_id,
                                 _checklist.c.periodo == periodo))
    return bool(session.connection().execute(stmt).scalar())


def conceptos_activos(session: Session, propiedad_id: UUID) -> list[UUID]:
    """ids de concepto_propiedad activos de la plantilla de la propiedad (RN-09)."""
    stmt = select(_concepto_propiedad.c.id).where(
        _concepto_propiedad.c.propiedad_id == propiedad_id,
        _concepto_propiedad.c.activo.is_(True),
    )
    return list(session.connection().execute(stmt).scalars())


def insertar_filas(session: Session, propiedad_id: UUID, periodo: date,
                   concepto_propiedad_ids: list[UUID]) -> None:
    """Una fila 'pendiente' por concepto. No confirma: el commit lo hace el service.

    ON CONFLICT DO NOTHING sobre UNIQUE (propiedad_id, periodo, concepto_propiedad_id):
    si dos aperturas simultáneas compiten, la segunda no duplica ni falla.
    """
    if not concepto_propiedad_ids:
        return
    valores = [{"propiedad_id": propiedad_id, "periodo": periodo,
                "concepto_propiedad_id": cp_id, "estado": "pendiente"}
               for cp_id in concepto_propiedad_ids]
    stmt = (pg_insert(_checklist).values(valores)
            .on_conflict_do_nothing(
                index_elements=["propiedad_id", "periodo", "concepto_propiedad_id"]))
    session.connection().execute(stmt)


def _select_filas():
    """Filas del checklist con el nombre del concepto y, si existe, su importe.

    Devuelve las columnas de FilaChecklist.
    """
    return (
        select(
            _checklist.c.id,
            _checklist.c.concepto_propiedad_id,
            _concepto.c.nombre.label("concepto"),
            _checklist.c.estado,
            _importe.c.id.label("importe_id"),
            _importe.c.importe,
        )
        .select_from(
            _checklist
            .join(_concepto_propiedad,
                  _concepto_propiedad.c.id == _checklist.c.concepto_propiedad_id)
            .join(_concepto, _concepto.c.id == _concepto_propiedad.c.concepto_id)
            .outerjoin(_importe, and_(
                _importe.c.concepto_propiedad_id == _checklist.c.concepto_propiedad_id,
                _importe.c.periodo == _checklist.c.periodo,
            ))
        )
    )


def filas(session: Session, propiedad_id: UUID, periodo: date):
    stmt = (_select_filas()
            .where(_checklist.c.propiedad_id == propiedad_id, _checklist.c.periodo == periodo)
            .order_by(_concepto.c.nombre))
    return session.connection().execute(stmt).mappings().all()


def fila(session: Session, fila_id: UUID):
    """Una fila con el formato de FilaChecklist, o None si no existe."""
    stmt = _select_filas().where(_checklist.c.id == fila_id)
    return session.connection().execute(stmt).mappings().first()


def fila_por_concepto(session: Session, propiedad_id: UUID, periodo: date,
                      concepto_propiedad_id: UUID):
    """{id, estado} de la fila del checklist para ese concepto, o None si no tiene fila.

    FOR UPDATE: bloquea la fila hasta el commit, para que otra operación sobre la misma
    fila (por ejemplo marcar no_corresponde) espere a que termine la carga.
    """
    stmt = (select(_checklist.c.id, _checklist.c.estado)
            .where(_checklist.c.propiedad_id == propiedad_id,
                   _checklist.c.periodo == periodo,
                   _checklist.c.concepto_propiedad_id == concepto_propiedad_id)
            .with_for_update())
    return session.connection().execute(stmt).mappings().first()


def fila_para_actualizar(session: Session, fila_id: UUID):
    """{id, propiedad_id, periodo, concepto_propiedad_id, estado} de la fila, o None.

    FOR UPDATE: bloquea la fila hasta el commit (mismo orden que la carga de importes:
    primero la fila del checklist, después el importe).
    """
    stmt = (select(_checklist.c.id, _checklist.c.propiedad_id, _checklist.c.periodo,
                   _checklist.c.concepto_propiedad_id, _checklist.c.estado)
            .where(_checklist.c.id == fila_id)
            .with_for_update())
    return session.connection().execute(stmt).mappings().first()


def cambiar_estado(session: Session, fila_id: UUID, estado: str) -> None:
    """No confirma: el commit lo hace el service que arma la transacción."""
    stmt = update(_checklist).where(_checklist.c.id == fila_id).values(estado=estado)
    session.connection().execute(stmt)
