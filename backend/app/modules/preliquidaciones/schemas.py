# modules/preliquidaciones/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.contract import Importe, Periodo, Porcentaje
from app.modules.advertencias.schemas import TipoAdvertencia


class PreliquidacionCrear(BaseModel):
    """HU-11 / HU-14: genera la versión siguiente (máxima + 1)."""
    propiedad_id: UUID
    periodo: Periodo
    confirmar_pendientes: bool = False


class DetalleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concepto_id: UUID
    concepto: str  # nombre del concepto, leído con join desde `concepto`
    importe: Importe


class AdvertenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: TipoAdvertencia
    detalle: str | None = None


class RepartoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    propietario_id: UUID
    nombre: str  # leído con join desde `propietario`
    porcentaje_aplicado: Porcentaje
    importe_correspondiente: Importe


class PreliquidacionResumen(BaseModel):
    """Cabecera de una versión (listado de versiones de HU-12)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    propiedad_id: UUID
    periodo: Periodo
    version: int
    importe_total: Importe
    generado_por: UUID
    generado_en: datetime


class PreliquidacionOut(PreliquidacionResumen):
    """Snapshot completo e inmutable de una versión."""
    detalle: list[DetalleOut]
    advertencias: list[AdvertenciaOut]
    reparto: list[RepartoOut]