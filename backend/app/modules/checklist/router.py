# modules/checklist/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.core.contract import Periodo, errores
from app.core.db import get_session
from app.core.errors import no_implementado
from app.modules.checklist import service
from app.modules.checklist.schemas import ChecklistAbrir, ChecklistOut, NoCorrespondeOut

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.post("", response_model=ChecklistOut, status_code=status.HTTP_201_CREATED,
             responses={200: {"model": ChecklistOut, "description": "El checklist ya existía"},
                        **errores(404)})
def abrir_periodo(datos: ChecklistAbrir, response: Response,
                  session: Session = Depends(get_session)):
    # HU-07: idempotente. 201 si se crea, 200 con el existente. Una fila por concepto activo.
    checklist, creado = service.abrir_periodo(session, datos.propiedad_id, datos.periodo)
    if not creado:
        response.status_code = status.HTTP_200_OK
    return checklist


@router.get("", response_model=ChecklistOut, responses=errores(404))
def obtener_checklist(propiedad_id: UUID, periodo: Periodo,
                      session: Session = Depends(get_session)):
    return service.obtener_checklist(session, propiedad_id, periodo)


@router.post("/{fila_id}/no-corresponde", response_model=NoCorrespondeOut,
             responses=errores(404))
def marcar_no_corresponde(fila_id: UUID):
    # HU-09 / RN-25: sobre pendiente o cargado; si estaba cargado borra el importe y lo audita,
    # todo en una transacción. Sobre no_corresponde responde 200 sin cambios.
    raise no_implementado()