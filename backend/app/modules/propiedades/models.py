# modules/propiedades/models.py
from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class Propiedad(SQLModel, table=True):
    __tablename__ = "propiedad"

    id: UUID = Field(primary_key=True)
    direccion: str
    localidad: str | None = None
    estado: str
    fecha_alta: datetime