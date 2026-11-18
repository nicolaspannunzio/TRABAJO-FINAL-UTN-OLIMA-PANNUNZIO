# modules/propiedades/schemas.py
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.contract import Porcentaje

Estado = Literal["activa", "inactiva"]


def _texto_obligatorio(v: str | None) -> str:
    """Sin espacios en los bordes y sin vacío. Un null explícito (PATCH) también se rechaza:
    la columna es NOT NULL. Los defaults no pasan por acá, así que omitir el campo sigue valiendo."""
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


# --- Propiedades ---------------------------------------------------------------

class PropiedadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    direccion: str
    localidad: str | None = None
    estado: Estado
    fecha_alta: datetime


class PropiedadCrear(BaseModel):
    direccion: str = Field(min_length=1)
    localidad: str | None = None
    estado: Estado = "activa"

    _direccion = field_validator("direccion")(_texto_obligatorio)
    _localidad = field_validator("localidad")(_texto_opcional)


class PropiedadActualizar(BaseModel):
    direccion: str | None = Field(default=None, min_length=1)
    localidad: str | None = None
    estado: Estado | None = None

    _direccion = field_validator("direccion")(_texto_obligatorio)
    _localidad = field_validator("localidad")(_texto_opcional)

    @field_validator("estado")
    @classmethod
    def _estado_no_null(cls, v):
        if v is None:
            raise ValueError("no puede ser null")
        return v


# --- Propietarios --------------------------------------------------------------

class PropietarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    cuit_dni: str | None = None
    email: str | None = None
    telefono: str | None = None
    estado: Estado


class PropietarioCrear(BaseModel):
    nombre: str = Field(min_length=1)
    cuit_dni: str | None = None
    email: str | None = None
    telefono: str | None = None

    _nombre = field_validator("nombre")(_texto_obligatorio)
    _opcionales = field_validator("cuit_dni", "email", "telefono")(_texto_opcional)


class PropietarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    cuit_dni: str | None = None
    email: str | None = None
    telefono: str | None = None

    _nombre = field_validator("nombre")(_texto_obligatorio)
    _opcionales = field_validator("cuit_dni", "email", "telefono")(_texto_opcional)


# --- Reparto vigente (HU-03, HU-04) -----------------------------------------------
# Propietario repetido y suma distinta de 100 los valida el service (422).

class RepartoEntrada(BaseModel):
    propietario_id: UUID
    porcentaje: Porcentaje


class RepartoVigente(BaseModel):
    propietario_id: UUID
    nombre: str
    porcentaje: Porcentaje