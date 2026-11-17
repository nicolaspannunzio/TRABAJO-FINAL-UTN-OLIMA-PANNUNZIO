# modules/propiedades/schemas.py
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.contract import Porcentaje

Estado = Literal["activa", "inactiva"]


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


class PropiedadActualizar(BaseModel):
    direccion: str | None = Field(default=None, min_length=1)
    localidad: str | None = None
    estado: Estado | None = None


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


class PropietarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    cuit_dni: str | None = None
    email: str | None = None
    telefono: str | None = None


# --- Reparto vigente (HU-03, HU-04) -----------------------------------------------
# Propietario repetido y suma distinta de 100 los valida el service (422).

class RepartoEntrada(BaseModel):
    propietario_id: UUID
    porcentaje: Porcentaje


class RepartoVigente(BaseModel):
    propietario_id: UUID
    nombre: str
    porcentaje: Porcentaje