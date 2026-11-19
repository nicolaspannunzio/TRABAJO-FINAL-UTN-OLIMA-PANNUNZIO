# modules/conceptos/schemas.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.contract import UmbralPct


def _nombre_obligatorio(v: str | None) -> str:
    """Sin espacios en los bordes y sin vacío. Un null explícito (PATCH) también se rechaza:
    la columna es NOT NULL. Omitir el campo en el PATCH sigue valiendo."""
    if v is None:
        raise ValueError("no puede ser null")
    v = v.strip()
    if not v:
        raise ValueError("no puede estar vacío")
    return v


def _texto_opcional(v: str | None) -> str | None:
    """Sin espacios en los bordes; una cadena vacía se guarda como null."""
    if v is None:
        return None
    return v.strip() or None


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

    _nombre = field_validator("nombre")(_nombre_obligatorio)
    _tipo = field_validator("tipo")(_texto_opcional)


class ConceptoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    tipo: str | None = None
    umbral_variacion_pct: UmbralPct | None = None

    _nombre = field_validator("nombre")(_nombre_obligatorio)
    _tipo = field_validator("tipo")(_texto_opcional)