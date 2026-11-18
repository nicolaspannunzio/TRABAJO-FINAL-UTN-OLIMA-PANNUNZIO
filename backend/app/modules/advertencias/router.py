# modules/advertencias/router.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.contract import Periodo, errores
from app.core.db import get_session
from app.modules.advertencias import service
from app.modules.advertencias.schemas import AdvertenciaPrevia

router = APIRouter(prefix="/advertencias", tags=["advertencias"])


@router.get("", response_model=list[AdvertenciaPrevia], responses=errores(404))
def vista_previa(propiedad_id: UUID, periodo: Periodo, session: Session = Depends(get_session)):
    # HU-10: variación contra el período anterior con el umbral efectivo; no persiste.
    return service.vista_previa(session, propiedad_id, periodo)
