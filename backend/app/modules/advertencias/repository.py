# modules/advertencias/repository.py
"""Lecturas para la vista previa de advertencias (HU-10).

advertencias no posee tablas (plan, sección 2): lee checklist_periodo e importe_mensual (B)
y concepto y concepto_propiedad (A) con table()/column() y joins explícitos (convención 2).
"""
from datetime import date
from uuid import UUID

from sqlalchemy import and_, column, exists, select, table
from sqlmodel import Session

_checklist = table("checklist_periodo", column("propiedad_id"), column("periodo"),
                   column("concepto_propiedad_id"), column("estado"))
_concepto_propiedad = table("concepto_propiedad", column("id"), column("concepto_id"))
_concepto = table("concepto", column("id"), column("nombre"), column("umbral_variacion_pct"))
_importe = table("importe_mensual", column("concepto_propiedad_id"), column("periodo"),
                 column("importe"))
_actual = _importe.alias("actual")
_anterior = _importe.alias("anterior")


def checklist_existe(session: Session, propiedad_id: UUID, periodo: date) -> bool:
    stmt = select(exists().where(_checklist.c.propiedad_id == propiedad_id,
                                 _checklist.c.periodo == periodo))
    return bool(session.connection().execute(stmt).scalar())


def conceptos_cargados(session: Session, propiedad_id: UUID, periodo: date, anterior: date):
    """Una fila por concepto `cargado` del período, con su importe y el del período anterior.

    Columnas: concepto_propiedad_id, concepto, umbral_variacion_pct, actual, anterior.
    `anterior` es None si ese mes no tiene importe (sin cargar o marcado no corresponde).
    Los conceptos pendiente y no_corresponde no tienen importe actual: no se evalúan.
    """
    stmt = (
        select(
            _checklist.c.concepto_propiedad_id,
            _concepto.c.nombre.label("concepto"),
            _concepto.c.umbral_variacion_pct,
            _actual.c.importe.label("actual"),
            _anterior.c.importe.label("anterior"),
        )
        .select_from(
            _checklist
            .join(_concepto_propiedad,
                  _concepto_propiedad.c.id == _checklist.c.concepto_propiedad_id)
            .join(_concepto, _concepto.c.id == _concepto_propiedad.c.concepto_id)
            .join(_actual, and_(
                _actual.c.concepto_propiedad_id == _checklist.c.concepto_propiedad_id,
                _actual.c.periodo == _checklist.c.periodo,
            ))
            .outerjoin(_anterior, and_(
                _anterior.c.concepto_propiedad_id == _checklist.c.concepto_propiedad_id,
                _anterior.c.periodo == anterior,
            ))
        )
        .where(_checklist.c.propiedad_id == propiedad_id,
               _checklist.c.periodo == periodo,
               _checklist.c.estado == "cargado")
        .order_by(_concepto.c.nombre)
    )
    return session.connection().execute(stmt).mappings().all()
