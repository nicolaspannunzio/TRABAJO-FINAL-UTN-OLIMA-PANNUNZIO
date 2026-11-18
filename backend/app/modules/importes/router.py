# modules/importes/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import errores
from app.core.db import get_session
from app.core.deps import Usuario, get_current_user
from app.core.errors import no_implementado
from app.modules.checklist.schemas import FilaChecklist
from app.modules.importes import service
from app.modules.importes.schemas import ImporteCorregir, ImporteCrear, ImporteOut

router = APIRouter(prefix="/importes", tags=["importes"])


@router.post("", response_model=FilaChecklist, status_code=status.HTTP_201_CREATED,
             responses=errores(409))
def cargar_importe(datos: ImporteCrear, session: Session = Depends(get_session),
                   usuario: Usuario = Depends(get_current_user)):
    # HU-08: inserta el importe, pasa la fila a `cargado` y audita, en una transacción.
    # 409 si ya hay importe para el par (se conserva el primero);
    # 422 si el concepto no tiene fila en el checklist del período.
    return service.cargar_importe(session, usuario.id, datos)


@router.patch("/{importe_id}", response_model=ImporteOut, responses=errores(404))
def corregir_importe(importe_id: UUID, datos: ImporteCorregir):
    raise no_implementado()
