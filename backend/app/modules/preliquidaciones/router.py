# modules/preliquidaciones/router.py
from uuid import UUID

from fastapi import APIRouter, status

from app.core.contract import Periodo, errores
from app.core.errors import no_implementado
from app.modules.preliquidaciones.schemas import (PreliquidacionCrear, PreliquidacionOut,
                                                  PreliquidacionResumen)

router = APIRouter(prefix="/preliquidaciones", tags=["preliquidaciones"])


@router.post("", response_model=PreliquidacionOut, status_code=status.HTTP_201_CREATED,
             responses=errores(404, 409))
def generar(datos: PreliquidacionCrear):
    # HU-11 / HU-14. Códigos 409: pendientes_sin_confirmar (detalle con la lista de
    # pendientes), periodo_sin_checklist, propiedad_sin_reparto, reparto_invalido.
    # 404: propiedad inexistente. Todo en una transacción y auditado.
    raise no_implementado()


@router.get("", response_model=list[PreliquidacionResumen], responses=errores(404))
def listar_versiones(propiedad_id: UUID, periodo: Periodo):
    raise no_implementado()


# Declarada antes que /{preliquidacion_id} para que "vigente" no se lea como un id.
@router.get("/vigente", response_model=PreliquidacionOut, responses=errores(404))
def obtener_vigente(propiedad_id: UUID, periodo: Periodo):
    raise no_implementado()


@router.get("/{preliquidacion_id}", response_model=PreliquidacionOut, responses=errores(404))
def obtener_version(preliquidacion_id: UUID):
    raise no_implementado()