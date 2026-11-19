# modules/propiedades/models.py
"""Tablas que posee el módulo propiedades (plan_implementacion.md, sección 2):
propiedad, propietario y propiedad_propietario (esta última la agrega A4).

El esquema sale de database/esquema_completo.sql (no se usa create_all()): los valores por
defecto del DDL (id, estado, fecha_alta) los pone la base.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Column, DateTime, Numeric, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class Propiedad(SQLModel, table=True):
    __tablename__ = "propiedad"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    direccion: str
    localidad: str | None = None
    estado: str = Field(default="activa")  # CHECK (estado IN ('activa', 'inactiva'))
    fecha_alta: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False,
                         server_default=text("now()")),
    )


class Propietario(SQLModel, table=True):
    __tablename__ = "propietario"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    nombre: str
    cuit_dni: str | None = None
    email: str | None = None
    telefono: str | None = None
    estado: str = Field(default="activa")  # CHECK (estado IN ('activa', 'inactiva'))


class PropiedadPropietario(SQLModel, table=True):
    __tablename__ = "propiedad_propietario"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    propiedad_id: UUID
    propietario_id: UUID
    porcentaje: Decimal = Field(sa_column=Column(Numeric(5, 2), nullable=False))