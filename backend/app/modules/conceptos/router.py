# modules/conceptos/router.py
from uuid import UUID

from fastapi import APIRouter, status

from app.core.contract import errores
from app.core.errors import no_implementado
from app.modules.conceptos.schemas import ConceptoActualizar, ConceptoCrear, ConceptoOut

router = APIRouter(prefix="/conceptos", tags=["conceptos"])


@router.get("", response_model=list[ConceptoOut])
def listar_conceptos():
    raise no_implementado()


@router.post("", response_model=ConceptoOut, status_code=status.HTTP_201_CREATED,
             responses=errores(409))
def crear_concepto(datos: ConceptoCrear):
    raise no_implementado()


@router.patch("/{concepto_id}", response_model=ConceptoOut, responses=errores(404, 409))
def actualizar_concepto(concepto_id: UUID, datos: ConceptoActualizar):
    raise no_implementado()