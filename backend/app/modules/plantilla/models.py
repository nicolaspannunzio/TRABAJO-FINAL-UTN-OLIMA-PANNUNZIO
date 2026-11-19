"""Tabla que posee el módulo plantilla (plan_implementacion.md, sección 2): concepto_propiedad.

El esquema sale de database/esquema_completo.sql (no se usa create_all()). propiedad_id y
concepto_id apuntan a tablas de otros módulos: se declaran sin foreign_key= (convención 3);
la clave foránea la hace cumplir la base.
"""
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class ConceptoPropiedad(SQLModel, table=True):
    __tablename__ = "concepto_propiedad"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    propiedad_id: UUID
    concepto_id: UUID
    activo: bool = True  # DEFAULT TRUE en el DDL