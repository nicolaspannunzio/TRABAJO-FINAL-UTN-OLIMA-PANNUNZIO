# modules/conceptos/schemas.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.contract import UmbralPct


class ConceptoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    tipo: str | None = None
    # None = usa el umbral global (UMBRAL_VARIACION_DEFAULT_PCT).
    umbral_variacion_pct: UmbralPct | None = None


class ConceptoCrear(BaseModel):
    nombre: str = Field(min_length=1)
    tipo: str | None = None
    umbral_variacion_pct: UmbralPct | None = None


class ConceptoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    tipo: str | None = None
    umbral_variacion_pct: UmbralPct | None = None