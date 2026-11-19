# modules/conceptos/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import errores
from app.core.db import get_session
from app.modules.conceptos import service
from app.modules.conceptos.schemas import ConceptoActualizar, ConceptoCrear, ConceptoOut

router = APIRouter(prefix="/conceptos", tags=["conceptos"])


@router.get("", response_model=list[ConceptoOut])
def listar_conceptos(session: Session = Depends(get_session)):
    return service.listar(session)


@router.post("", response_model=ConceptoOut, status_code=status.HTTP_201_CREATED,
             responses=errores(409))
def crear_concepto(datos: ConceptoCrear, session: Session = Depends(get_session)):
    return service.crear(session, datos)


@router.patch("/{concepto_id}", response_model=ConceptoOut, responses=errores(404, 409))
def actualizar_concepto(concepto_id: UUID, datos: ConceptoActualizar,
                        session: Session = Depends(get_session)):
    return service.actualizar(session, concepto_id, datos)