from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, SQLModel


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id: UUID | None = Field(
    default=None,
    sa_column=Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
)
    # usuario_id apunta a una tabla de otro módulo: sin foreign_key= (convención 3)
    usuario_id: UUID
    accion: str
    entidad: str
    entidad_id: UUID | None = None
    detalle: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    fecha: datetime | None = None