# modules/plantilla/router.py
from uuid import UUID

from fastapi import APIRouter, status

from app.core.contract import errores
from app.core.errors import no_implementado
from app.modules.plantilla.schemas import (ConceptoPropiedadActualizar, ConceptoPropiedadCrear,
                                           ConceptoPropiedadOut)

router = APIRouter(prefix="/propiedades/{propiedad_id}/conceptos", tags=["plantilla"])


@router.get("", response_model=list[ConceptoPropiedadOut], responses=errores(404))
def listar_plantilla(propiedad_id: UUID):
    raise no_implementado()


@router.post("", response_model=ConceptoPropiedadOut, status_code=status.HTTP_201_CREATED,
             responses=errores(404, 409))
def asociar_concepto(propiedad_id: UUID, datos: ConceptoPropiedadCrear):
    raise no_implementado()


@router.patch("/{concepto_propiedad_id}", response_model=ConceptoPropiedadOut,
              responses=errores(404))
def actualizar_concepto_propiedad(propiedad_id: UUID, concepto_propiedad_id: UUID,
                                  datos: ConceptoPropiedadActualizar):
    raise no_implementado()