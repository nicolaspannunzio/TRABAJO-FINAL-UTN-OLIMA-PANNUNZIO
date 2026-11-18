# modules/preliquidaciones/repository.py
"""Acceso a datos de la preliquidación (HU-11, y la lectura que usa HU-12).

Tablas de otros módulos (convención 2), leídas con table()/column():
- propiedad, propietario, propiedad_propietario, concepto, concepto_propiedad: A.
- checklist_periodo, importe_mensual: B (checklist e importes).
"""
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, column, exists, func, insert, select, table
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.modules.preliquidaciones.models import (Preliquidacion, PreliquidacionAdvertencia,
                                                 PreliquidacionDetalle, Reparto)

_propiedad = table("propiedad", column("id"))
_propietario = table("propietario", column("id"), column("nombre"))
_propiedad_propietario = table("propiedad_propietario", column("propiedad_id"),
                               column("propietario_id"), column("porcentaje"))
_concepto = table("concepto", column("id"), column("nombre"))
_concepto_propiedad = table("concepto_propiedad", column("id"), column("concepto_id"))
_checklist = table("checklist_periodo", column("propiedad_id"), column("periodo"),
                   column("concepto_propiedad_id"), column("estado"))
_importe = table("importe_mensual", column("concepto_propiedad_id"), column("periodo"),
                 column("importe"))

_cabecera = Preliquidacion.__table__
_detalle = PreliquidacionDetalle.__table__
_advertencia = PreliquidacionAdvertencia.__table__
_reparto = Reparto.__table__

# UNIQUE (propiedad_id, periodo, version) de esquema_completo.sql (nombre por defecto).
_UQ_VERSION = "preliquidacion_propiedad_id_periodo_version_key"


class VersionEnConflicto(Exception):
    """Otra generación simultánea tomó el mismo número de versión."""


# --- Lecturas para generar -----------------------------------------------------

def propiedad_existe(session: Session, propiedad_id: UUID) -> bool:
    stmt = select(exists().where(_propiedad.c.id == propiedad_id))
    return bool(session.connection().execute(stmt).scalar())


def filas_checklist(session: Session, propiedad_id: UUID, periodo: date):
    """Filas del checklist con su concepto y, si está cargado, su importe.

    Columnas: concepto_propiedad_id, concepto_id, concepto, estado, importe.
    """
    stmt = (
        select(_checklist.c.concepto_propiedad_id, _concepto.c.id.label("concepto_id"),
               _concepto.c.nombre.label("concepto"), _checklist.c.estado, _importe.c.importe)
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
        .where(_checklist.c.propiedad_id == propiedad_id, _checklist.c.periodo == periodo)
        .order_by(_concepto.c.nombre)
    )
    return session.connection().execute(stmt).mappings().all()


def reparto_vigente(session: Session, propiedad_id: UUID) -> dict[UUID, Decimal]:
    """{propietario_id: porcentaje} vigente de la propiedad (tabla de A)."""
    stmt = (select(_propiedad_propietario.c.propietario_id, _propiedad_propietario.c.porcentaje)
            .where(_propiedad_propietario.c.propiedad_id == propiedad_id))
    return {r.propietario_id: r.porcentaje for r in session.connection().execute(stmt)}


def siguiente_version(session: Session, propiedad_id: UUID, periodo: date) -> int:
    """Versión máxima + 1, o 1 si es la primera (RN-22)."""
    stmt = (select(func.coalesce(func.max(_cabecera.c.version), 0) + 1)
            .where(_cabecera.c.propiedad_id == propiedad_id, _cabecera.c.periodo == periodo))
    return int(session.connection().execute(stmt).scalar_one())


# --- Escrituras (solo INSERT: el snapshot es inmutable) -------------------------

def insertar_cabecera(session: Session, propiedad_id: UUID, periodo: date, version: int,
                      importe_total: Decimal, generado_por: UUID) -> UUID:
    """No confirma. Si otra generación ya tomó esa versión, lanza VersionEnConflicto."""
    stmt = (insert(_cabecera)
            .values(propiedad_id=propiedad_id, periodo=periodo, version=version,
                    importe_total=importe_total, generado_por=generado_por)
            .returning(_cabecera.c.id))
    try:
        return session.connection().execute(stmt).scalar_one()
    except IntegrityError as e:
        diag = getattr(e.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == _UQ_VERSION:
            raise VersionEnConflicto from e
        raise


def insertar_detalle(session: Session, preliquidacion_id: UUID,
                     filas: list[tuple[UUID, Decimal]]) -> None:
    """filas: [(concepto_id, importe)]."""
    if filas:
        session.connection().execute(insert(_detalle), [
            {"preliquidacion_id": preliquidacion_id, "concepto_id": c, "importe": i}
            for c, i in filas
        ])


def insertar_advertencias(session: Session, preliquidacion_id: UUID,
                          advertencias: list[tuple[str, str | None]]) -> None:
    """advertencias: [(tipo, detalle)]."""
    if advertencias:
        session.connection().execute(insert(_advertencia), [
            {"preliquidacion_id": preliquidacion_id, "tipo": t, "detalle": d}
            for t, d in advertencias
        ])


def insertar_reparto(session: Session, preliquidacion_id: UUID,
                     cuotas: list[tuple[UUID, Decimal, Decimal]]) -> None:
    """cuotas: [(propietario_id, porcentaje_aplicado, importe_correspondiente)]."""
    session.connection().execute(insert(_reparto), [
        {"preliquidacion_id": preliquidacion_id, "propietario_id": p,
         "porcentaje_aplicado": pct, "importe_correspondiente": imp}
        for p, pct, imp in cuotas
    ])


# --- Lectura de una versión completa (la reutiliza HU-12) ------------------------

def obtener(session: Session, preliquidacion_id: UUID) -> dict | None:
    """Cabecera, detalle, advertencias y reparto de una versión, tal como se guardaron.

    Solo lee las 4 tablas del snapshot (más los nombres de concepto y propietario): nunca
    `auditoria` ni `importe_mensual`, así una corrección posterior no la altera.
    """
    conn = session.connection()
    cabecera = conn.execute(
        select(_cabecera).where(_cabecera.c.id == preliquidacion_id)
    ).mappings().first()
    if cabecera is None:
        return None

    detalle = conn.execute(
        select(_detalle.c.concepto_id, _concepto.c.nombre.label("concepto"), _detalle.c.importe)
        .select_from(_detalle.join(_concepto, _concepto.c.id == _detalle.c.concepto_id))
        .where(_detalle.c.preliquidacion_id == preliquidacion_id)
        .order_by(_concepto.c.nombre)
    ).mappings().all()

    advertencias = conn.execute(
        select(_advertencia.c.tipo, _advertencia.c.detalle)
        .where(_advertencia.c.preliquidacion_id == preliquidacion_id)
        .order_by(_advertencia.c.tipo, _advertencia.c.detalle)
    ).mappings().all()

    reparto = conn.execute(
        select(_reparto.c.propietario_id, _propietario.c.nombre, _reparto.c.porcentaje_aplicado,
               _reparto.c.importe_correspondiente)
        .select_from(_reparto.join(_propietario, _propietario.c.id == _reparto.c.propietario_id))
        .where(_reparto.c.preliquidacion_id == preliquidacion_id)
        .order_by(_reparto.c.propietario_id)
    ).mappings().all()

    return {**cabecera, "detalle": detalle, "advertencias": advertencias, "reparto": reparto}
