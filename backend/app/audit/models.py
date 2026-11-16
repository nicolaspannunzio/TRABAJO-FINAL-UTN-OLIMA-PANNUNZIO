from datetime import datetime
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id: UUID | None = Field(default=None, primary_key=True)
    # usuario_id apunta a una tabla de otro módulo: sin foreign_key= (convención 3)
    usuario_id: UUID
    accion: str
    entidad: str
    entidad_id: UUID | None = None
    detalle: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    fecha: datetime | None = None