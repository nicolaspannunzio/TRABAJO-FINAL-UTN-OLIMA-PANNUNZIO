# modules/importes/models.py
"""Tablas que posee el módulo importes (plan_implementacion.md, sección 2): importe_mensual.

El esquema sale de database/esquema_completo.sql (no se usa create_all()).
concepto_propiedad_id (plantilla, A) y cargado_por (usuarios, A) apuntan a tablas de
otro módulo: se declaran SIN foreign_key= (convención 3); la base hace cumplir las FK.
UNIQUE (concepto_propiedad_id, periodo) vive en el índice uq_importe_concepto_periodo.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Column, DateTime, Numeric, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class ImporteMensual(SQLModel, table=True):
    __tablename__ = "importe_mensual"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    concepto_propiedad_id: UUID
    periodo: date  # siempre AAAA-MM-01 (RN-01; CHECK ck_importe_periodo_primer_dia)
    # NUMERIC(14,2), sin CHECK de signo: admite negativos (notas de crédito) y 0.
    importe: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    cargado_por: UUID
    fecha_carga: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False,
                         server_default=text("now()")),
    )
