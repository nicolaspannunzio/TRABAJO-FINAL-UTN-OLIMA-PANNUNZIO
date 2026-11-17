# modules/importes/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.contract import Importe, Periodo


class ImporteCrear(BaseModel):
    """HU-08: admite negativos (notas de crédito) y 0."""
    propiedad_id: UUID
    periodo: Periodo
    concepto_propiedad_id: UUID
    importe: Importe


class ImporteCorregir(BaseModel):
    """HU-13: la auditoría guarda el valor anterior."""
    importe: Importe


class ImporteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    concepto_propiedad_id: UUID
    periodo: Periodo
    importe: Importe
    cargado_por: UUID
    fecha_carga: datetime