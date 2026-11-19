# modules/preliquidaciones/models.py
"""Tablas que posee el módulo preliquidaciones (plan_implementacion.md, sección 2):
preliquidacion, preliquidacion_detalle, preliquidacion_advertencia y reparto.

Son el snapshot inmutable de cada versión: la base rechaza UPDATE, DELETE y TRUNCATE con
triggers (esquema_completo.sql). Este módulo solo inserta.

FK a tablas de otros módulos (propiedad, concepto, propietario: A; usuario: A) sin
foreign_key= (convención 3). Las FK entre las 4 tablas de este módulo también se omiten:
las inserciones usan Core y el DDL es la fuente de verdad.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Column, DateTime, Numeric, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


def _id_generado():
    return Field(default=None, sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                                                server_default=text("gen_random_uuid()")))


def _dinero(nullable: bool = False):
    return Field(sa_column=Column(Numeric(14, 2), nullable=nullable))


class Preliquidacion(SQLModel, table=True):
    __tablename__ = "preliquidacion"

    id: UUID | None = _id_generado()
    propiedad_id: UUID
    periodo: date
    version: int
    importe_total: Decimal = _dinero()
    generado_por: UUID
    generado_en: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("now()")),
    )


class PreliquidacionDetalle(SQLModel, table=True):
    __tablename__ = "preliquidacion_detalle"

    id: UUID | None = _id_generado()
    preliquidacion_id: UUID
    concepto_id: UUID
    importe: Decimal = _dinero()


class PreliquidacionAdvertencia(SQLModel, table=True):
    __tablename__ = "preliquidacion_advertencia"

    id: UUID | None = _id_generado()
    preliquidacion_id: UUID
    tipo: str  # variacion_inusual | sin_referencia | total_negativo | pendiente_confirmado
    detalle: str | None = None


class Reparto(SQLModel, table=True):
    __tablename__ = "reparto"

    id: UUID | None = _id_generado()
    preliquidacion_id: UUID
    propietario_id: UUID
    porcentaje_aplicado: Decimal = Field(sa_column=Column(Numeric(5, 2), nullable=False))
    importe_correspondiente: Decimal = _dinero()
