# modules/advertencias/schemas.py
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# Mismos valores que el CHECK de preliquidacion_advertencia.tipo.
# La vista previa (HU-10) solo produce variacion_inusual y sin_referencia;
# total_negativo y pendiente_confirmado aparecen al generar la preliquidación (HU-11).
TipoAdvertencia = Literal["variacion_inusual", "sin_referencia",
                          "total_negativo", "pendiente_confirmado"]


class AdvertenciaPrevia(BaseModel):
    """HU-10: vista previa, no se persiste ni bloquea."""
    concepto_propiedad_id: UUID
    tipo: TipoAdvertencia
    detalle: str | None = None