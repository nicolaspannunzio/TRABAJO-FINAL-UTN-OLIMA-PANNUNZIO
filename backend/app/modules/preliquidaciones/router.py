# modules/preliquidaciones/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import Periodo, errores
from app.core.db import get_session
from app.core.deps import Usuario, get_current_user
from app.modules.preliquidaciones import service
from app.modules.preliquidaciones.schemas import (PreliquidacionCrear, PreliquidacionOut,
                                                  PreliquidacionResumen)

router = APIRouter(prefix="/preliquidaciones", tags=["preliquidaciones"])


@router.post("", response_model=PreliquidacionOut, status_code=status.HTTP_201_CREATED,
             responses=errores(404, 409))
def generar(datos: PreliquidacionCrear, session: Session = Depends(get_session),
            usuario: Usuario = Depends(get_current_user)):
    # HU-11 / HU-14. Códigos 409: pendientes_sin_confirmar (detalle con la lista de
    # pendientes), periodo_sin_checklist, propiedad_sin_reparto, reparto_invalido,
    # version_en_conflicto. 404: propiedad inexistente. Todo en una transacción y auditado.
    return service.generar(session, usuario.id, datos)


@router.get("", response_model=list[PreliquidacionResumen], responses=errores(404))
def listar_versiones(propiedad_id: UUID, periodo: Periodo,
                     session: Session = Depends(get_session)):
    # HU-12: cabeceras de todas las versiones, de la 1 en adelante; [] si no hay ninguna.
    return service.listar_versiones(session, propiedad_id, periodo)


# Declarada antes que /{preliquidacion_id} para que "vigente" no se lea como un id.
@router.get("/vigente", response_model=PreliquidacionOut, responses=errores(404))
def obtener_vigente(propiedad_id: UUID, periodo: Periodo,
                    session: Session = Depends(get_session)):
    # HU-12: la versión de mayor número (vista preliquidacion_vigente).
    return service.obtener_vigente(session, propiedad_id, periodo)


@router.get("/{preliquidacion_id}", response_model=PreliquidacionOut, responses=errores(404))
def obtener_version(preliquidacion_id: UUID, session: Session = Depends(get_session)):
    # HU-12: una versión tal como se generó, leída solo del snapshot (nunca de auditoria).
    return service.obtener(session, preliquidacion_id)