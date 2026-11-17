# modules/plantilla/schemas.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConceptoPropiedadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    propiedad_id: UUID
    concepto_id: UUID
    concepto: str  # nombre del concepto, leído con join desde `concepto`
    activo: bool


class ConceptoPropiedadCrear(BaseModel):
    concepto_id: UUID


class ConceptoPropiedadActualizar(BaseModel):
    activo: bool