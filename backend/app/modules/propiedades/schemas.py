# modules/propiedades/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PropiedadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    direccion: str
    localidad: str | None = None
    estado: str
    fecha_alta: datetime