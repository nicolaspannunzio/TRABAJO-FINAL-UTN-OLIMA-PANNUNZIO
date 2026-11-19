# modules/plantilla/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import errores
from app.core.db import get_session
from app.modules.plantilla import service
from app.modules.plantilla.schemas import (
    ConceptoPropiedadActualizar,
    ConceptoPropiedadCrear,
    ConceptoPropiedadOut,
)

router = APIRouter(prefix="/propiedades/{propiedad_id}/conceptos", tags=["plantilla"])


@router.get("", response_model=list[ConceptoPropiedadOut], responses=errores(404))
def listar_plantilla(propiedad_id: UUID, session: Session = Depends(get_session)):
    return service.listar(session, propiedad_id)


@router.post("", response_model=ConceptoPropiedadOut, status_code=status.HTTP_201_CREATED,
             responses=errores(404, 409))
def asociar_concepto(propiedad_id: UUID, datos: ConceptoPropiedadCrear,
                     session: Session = Depends(get_session)):
    return service.asociar(session, propiedad_id, datos)


@router.patch("/{concepto_propiedad_id}", response_model=ConceptoPropiedadOut,
              responses=errores(404))
def actualizar_concepto_propiedad(propiedad_id: UUID, concepto_propiedad_id: UUID,
                                  datos: ConceptoPropiedadActualizar,
                                  session: Session = Depends(get_session)):
    return service.actualizar(session, propiedad_id, concepto_propiedad_id, datos)