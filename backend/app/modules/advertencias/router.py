# modules/advertencias/router.py
from uuid import UUID

from fastapi import APIRouter

from app.core.contract import Periodo, errores
from app.core.errors import no_implementado
from app.modules.advertencias.schemas import AdvertenciaPrevia

router = APIRouter(prefix="/advertencias", tags=["advertencias"])


@router.get("", response_model=list[AdvertenciaPrevia], responses=errores(404))
def vista_previa(propiedad_id: UUID, periodo: Periodo):
    # HU-10: variación contra el período anterior con el umbral efectivo; no persiste.
    raise no_implementado()