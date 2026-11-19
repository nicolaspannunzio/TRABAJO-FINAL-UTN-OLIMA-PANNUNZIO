# modules/conceptos/models.py
"""Tabla que posee el módulo conceptos (plan_implementacion.md, sección 2): concepto.

El esquema sale de database/esquema_completo.sql (no se usa create_all()): el id lo genera la base.
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Column, Numeric, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class Concepto(SQLModel, table=True):
    __tablename__ = "concepto"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    nombre: str  # UNIQUE en el DDL
    tipo: str | None = None
    # NUMERIC(5,2) CHECK (> 0). NULL = usa el umbral global.
    umbral_variacion_pct: Decimal | None = Field(default=None, sa_column=Column(Numeric(5, 2)))