# modules/usuarios/models.py
"""Tablas que posee el módulo usuarios (plan_implementacion.md, sección 2): rol y usuario.

El esquema sale de database/esquema_completo.sql (no se usa create_all()).
usuario.id es el mismo UUID que auth.users.id (RN-02): no tiene default, lo da Supabase Auth,
y la FK hacia auth.users la hace cumplir la base (no se declara foreign_key= acá).
rol_id apunta a `rol`, que es del mismo módulo, así que sí puede declararla.
"""
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True,
                         server_default=text("gen_random_uuid()")),
    )
    nombre: str  # UNIQUE en la base: 'admin' u 'operador'


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), primary_key=True))
    nombre: str
    email: str  # UNIQUE en la base (usuario_email_key)
    rol_id: UUID = Field(foreign_key="rol.id")
    activo: bool = True
