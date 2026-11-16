# modules/propiedades/router.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.modules.propiedades import service
from app.modules.propiedades.schemas import PropiedadOut

router = APIRouter(prefix="/propiedades", tags=["propiedades"])


@router.get("", response_model=list[PropiedadOut])
def listar(session: Session = Depends(get_session)):
    return service.listar(session)