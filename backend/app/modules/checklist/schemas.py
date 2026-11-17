# modules/checklist/schemas.py
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.contract import Importe, Periodo

EstadoChecklist = Literal["pendiente", "cargado", "no_corresponde"]


class ChecklistAbrir(BaseModel):
    """HU-07: abrir el período. Un período que no es AAAA-MM-01 se rechaza con 422."""
    propiedad_id: UUID
    periodo: Periodo


class FilaChecklist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    concepto_propiedad_id: UUID
    concepto: str  # nombre del concepto, leído con join desde `concepto`
    estado: EstadoChecklist
    importe_id: UUID | None = None  # solo si estado = cargado
    importe: Importe | None = None


class ChecklistOut(BaseModel):
    propiedad_id: UUID
    periodo: Periodo
    filas: list[FilaChecklist]


class NoCorrespondeOut(FilaChecklist):
    """HU-09: la fila queda en no_corresponde, sin importe.

    Si estaba `cargado`, `importe_eliminado` trae el valor borrado (también queda en auditoría).
    Si ya estaba `no_corresponde`, la respuesta es idempotente: estado_anterior = no_corresponde.
    """
    estado_anterior: EstadoChecklist
    importe_eliminado: Importe | None = None